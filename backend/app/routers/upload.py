from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from typing import List
from app import schemas, crud, models
from app.database import get_db, SessionLocal
from app.ml.menu_analyzer import run_menu_engineering
from app.ml.forecaster import run_demand_forecast
from app.ml.demo_seeder import seed_demo_data
from app.ml.rag_engine import rag_engine
from app.logger import logger

router = APIRouter(prefix="/upload", tags=["upload"])

# Seed the recent window instantly (snappy first paint), then extend to a
# longer history in the background - more history meaningfully improves the
# forecast, but generating and querying it costs memory. On a memory-limited
# host (e.g. Render's 512 MB free tier) FULL_SEED_DAYS is set lower via env so
# the dataset + ML training fit in RAM; locally it defaults to a full year.
QUICK_SEED_DAYS = int(os.getenv("QUICK_SEED_DAYS", "30"))
FULL_SEED_DAYS = int(os.getenv("FULL_SEED_DAYS", "365"))

_seed_status: dict = {
    "in_progress": False,
    "preset": None,
    "days_seeded": None,
}


def run_async_ml_training(db: Session):
    """Run Menu Engineering and Demand Forecasting models and cache results in DB."""
    logger.info("Starting background ML model training task...")
    try:
        # 1. Run K-Means Menu Engineering
        analyses = run_menu_engineering(db)
        if analyses:
            crud.update_menu_analysis(db, analyses)
            logger.info(f"Successfully updated Menu Engineering results for {len(analyses)} items.")
            
        # 2. Run Time Series Forecasting
        forecasts = run_demand_forecast(db)
        if forecasts:
            crud.update_demand_forecast(db, forecasts)
            logger.info(f"Successfully updated Demand Forecasts for next {len(forecasts)} days.")

        rag_engine.refresh_from_db(db)
        logger.info("RAG knowledge base refreshed after ML training.")
            
        logger.info("Background ML model training completed successfully.")
    except Exception as e:
        logger.error(f"Error occurred during background ML training: {str(e)}")


# Standardize column naming mappings for various CRM formats (iiko, R-Keeper, МойСклад)
COLUMN_MAPPINGS = {
    # Order/Check ID
    "order_id": "order_id_crm",
    "check_id": "order_id_crm",
    "id чека": "order_id_crm",
    "номер чека": "order_id_crm",
    "номер": "order_id_crm",
    
    # Timestamp
    "timestamp": "timestamp",
    "date": "timestamp",
    "datetime": "timestamp",
    "дата": "timestamp",
    "время": "timestamp",
    "дата и время": "timestamp",
    
    # Item Name
    "item_name": "item_name",
    "position": "item_name",
    "product": "item_name",
    "номенклатура": "item_name",
    "наименование": "item_name",
    "блюдо": "item_name",
    
    # Price
    "price": "price",
    "цена": "price",
    "стоимость": "price",
    
    # Quantity
    "quantity": "quantity",
    "qty": "quantity",
    "amount": "quantity",
    "количество": "quantity",
    "кол-во": "quantity",
    
    # Category (Optional)
    "category": "category",
    "group": "category",
    "категория": "category",
    "группа": "category",
    "родительская группа": "category"
}

@router.post("/checks", response_model=schemas.UploadStatus)
async def upload_checks(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload receipts CSV/XLSX file, parse, validate, and write to database.
    Triggers ML model re-training in the background.
    """
    contents = await file.read()
    filename = file.filename.lower()
    
    # 1. Read file into Pandas
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # 2. Map Columns dynamically
    df.columns = [col.strip().lower() for col in df.columns]
    mapped_cols = {}
    for col in df.columns:
        if col in COLUMN_MAPPINGS:
            mapped_cols[col] = COLUMN_MAPPINGS[col]
            
    # Check for mandatory columns
    required = ["order_id_crm", "timestamp", "item_name", "price", "quantity"]
    missing = [req for req in required if req not in mapped_cols.values()]
    if missing:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required columns in upload. Could not map fields: {missing}. Available columns: {list(df.columns)}"
        )

    # Rename mapped columns and drop unmapped to clean df
    inverse_mapping = {v: k for k, v in COLUMN_MAPPINGS.items() if k in df.columns}
    # Since dict comprehension might have duplicates, build a clean mapper
    clean_mapper = {}
    for col in df.columns:
        if col in COLUMN_MAPPINGS:
            clean_mapper[col] = COLUMN_MAPPINGS[col]
            
    df = df.rename(columns=clean_mapper)
    df = df[list(required) + (["category"] if "category" in df.columns else [])]
    
    if "category" not in df.columns:
        df["category"] = "Other"
    else:
        df["category"] = df["category"].fillna("Other")

    # 3. Process records
    # Group items by order to structure them inside OrderCreate schema
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    orders_processed = 0
    items_processed = 0
    errors = []
    
    grouped = df.groupby("order_id_crm")
    
    for order_id_crm, group in grouped:
        try:
            # Aggregate items
            items_list = []
            order_total = 0.0
            order_timestamp = None
            
            for _, row in group.iterrows():
                if order_timestamp is None:
                    order_timestamp = row["timestamp"]
                
                price = float(row["price"])
                qty = int(row["quantity"])
                total_price = price * qty
                order_total += total_price
                
                item_in = schemas.OrderItemCreate(
                    item_name=str(row["item_name"]),
                    category=str(row["category"]),
                    price=price,
                    quantity=qty,
                    total_price=total_price
                )
                items_list.append(item_in)
            
            order_in = schemas.OrderCreate(
                order_id_crm=str(order_id_crm),
                timestamp=order_timestamp,
                total_amount=order_total,
                payment_method="Cash/Card",  # Default placeholder
                items=items_list
            )
            
            # Write to Database
            crud.create_order(db, order_in)
            orders_processed += 1
            items_processed += len(items_list)
            
        except Exception as e:
            errors.append(f"Error processing order {order_id_crm}: {str(e)}")
            
    # Commit database transactions
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction error: {str(e)}")

    # 4. Trigger Background ML Training tasks (re-calculates K-Means & Time Series)
    if orders_processed > 0:
        background_tasks.add_task(run_async_ml_training, db)

    return schemas.UploadStatus(
        success=True,
        message=f"Ingestion completed. Enqueued ML model training.",
        orders_processed=orders_processed,
        items_processed=items_processed,
        errors=errors[:10]  # Return first 10 errors if any
    )


def _train_and_extend_background(preset_name: str, quick_window_start: datetime):
    """Runs after the response is already sent (own DB session). Order matters
    for a snappy UI on a slow free-tier CPU:
      1. Train on the quick 30-day window first, so Menu Engineering and the
         forecast appear within a few seconds.
      2. Seed the older history behind that window.
      3. Retrain on the full history and refresh the RAG corpus.
    Training is deliberately OFF the request path: on a 0.15 CPU instance it can
    take tens of seconds, and doing it inside /seed-demo blocked the worker long
    enough that concurrent /stats and /history calls timed out (502), which the
    dashboard then rendered as $NaN / $undefined."""
    db = SessionLocal()
    try:
        # 1. Quick-window training so the dashboard fills in fast.
        run_async_ml_training(db)
        rag_engine.refresh_from_db(db)

        # 2. Extend the older history behind the quick window.
        seed_demo_data(
            db,
            days=FULL_SEED_DAYS - QUICK_SEED_DAYS,
            preset_name=preset_name,
            end_date=quick_window_start,
            clean_first=False,
        )

        # 3. Retrain on the full history and refresh RAG with the richer data.
        run_async_ml_training(db)
        rag_engine.refresh_from_db(db)
        logger.info(f"Background seed + training completed for preset '{preset_name}'.")
    except Exception as e:
        logger.error(f"Background seed/training failed: {e}")
    finally:
        _seed_status["in_progress"] = False
        db.close()


@router.get("/seed-status")
def get_seed_status():
    """Lets the frontend know whether the full-year background seed is still running."""
    return _seed_status


@router.post("/seed-demo")
async def seed_demo(
    background_tasks: BackgroundTasks,
    preset_name: str = "Casual Coffee Shop",
    db: Session = Depends(get_db)
):
    """Seed the last 30 days instantly so the dashboard has something to show
    right away, then extend to a full year of history in the background."""
    try:
        now = datetime.now()
        # Quick 30-day seed only - just the DB writes, no model training. This
        # returns in a couple of seconds so the dashboard's /stats and /history
        # calls get fresh data immediately; training happens off the request
        # path in the background task below.
        stats = seed_demo_data(db, days=QUICK_SEED_DAYS, preset_name=preset_name, end_date=now, clean_first=True)

        quick_window_start = now - timedelta(days=QUICK_SEED_DAYS)
        _seed_status.update({"in_progress": True, "preset": preset_name, "days_seeded": QUICK_SEED_DAYS})
        background_tasks.add_task(_train_and_extend_background, preset_name, quick_window_start)

        return {
            "success": True,
            "message": f"Demo database seeded with the last {QUICK_SEED_DAYS} days of {preset_name}. Training models and loading more history in the background...",
            "orders_seeded": stats["orders_seeded"],
            "items_seeded": stats["items_seeded"],
            "days_seeded": stats["days_seeded"],
            "background_extension_in_progress": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {str(e)}")
