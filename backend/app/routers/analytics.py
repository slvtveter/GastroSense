from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Dict, Any
from app import schemas, crud, models
from app.database import get_db
from app.ml.forecaster import get_last_model_info
from app.ml.market_basket import compute_associations

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/forecast-info")
def get_forecast_model_info():
    """Explain which model produced the current forecast and why it was chosen."""
    return get_last_model_info()

@router.get("/menu", response_model=List[schemas.MenuAnalysisResponse])
def get_menu_analysis(db: Session = Depends(get_db)):
    """Retrieve K-Means Menu Engineering results."""
    return crud.get_menu_analysis(db)


@router.get("/forecast", response_model=List[schemas.DemandForecastResponse])
def get_demand_forecast(db: Session = Depends(get_db)):
    """Retrieve 7-day demand forecasts."""
    return crud.get_demand_forecast(db)


@router.get("/stats")
def get_restaurant_stats(db: Session = Depends(get_db)):
    """Compute high-level restaurant stats (revenue, order counts, averages)."""
    # Total Revenue and Orders
    stats = db.query(
        func.sum(models.Order.total_amount).label("total_revenue"),
        func.count(models.Order.id).label("total_orders")
    ).first()
    
    total_revenue = float(stats.total_revenue or 0.0)
    total_orders = int(stats.total_orders or 0)
    avg_check = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    
    # Total Unique Items Sold
    total_items = db.query(models.OrderItem).count()
    
    # Average items per check
    avg_items_per_check = 0.0
    if total_orders > 0:
        total_qty = db.query(func.sum(models.OrderItem.quantity)).scalar() or 0
        avg_items_per_check = round(total_qty / total_orders, 1)

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_check": avg_check,
        "total_items_sold": total_items,
        "avg_items_per_check": avg_items_per_check
    }


@router.get("/history")
def get_historical_sales(db: Session = Depends(get_db), days: int = 30):
    """Retrieve daily historical revenue and orders for the last N days."""
    sql = f"""
        SELECT 
            DATE(timestamp) as date,
            SUM(total_amount) as revenue,
            COUNT(*) as orders_count
        FROM orders
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT {days}
    """
    result = db.execute(text(sql)).fetchall()
    
    # Reverse to chronological order
    result = result[::-1]
    
    return [
        {
            "date": str(row[0]),
            "revenue": float(row[1] or 0.0),
            "orders_count": int(row[2] or 0)
        } for row in result
    ]


@router.get("/associations")
def get_item_associations(db: Session = Depends(get_db)):
    """Perform Market Basket Analysis to compute conditional probabilities of item pairs.
    Returns:
    - data: P(Item B | Item A) - confidence, the probability of ordering Item B if Item A is ordered.
    - lift: how many times more often A and B are bought together than random chance would predict
      (>1 = real synergy, <1 = bought together less than chance, i.e. not a real combo).
    - support: raw count of orders containing both A and B - used to filter out pairs that only
      look strong because one of the items is rarely ordered (small-sample noise).
    """
    return compute_associations(db)
