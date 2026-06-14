from sqlalchemy.orm import Session
from sqlalchemy import delete
from typing import List, Dict, Any
from datetime import datetime
from app import models, schemas

# --- Receipt / Ingestion CRUD ---

def create_order(db: Session, order_in: schemas.OrderCreate) -> models.Order:
    """Create a new order and its corresponding order items in the database.
    Skips if order_id_crm already exists.
    """
    # Check if order already exists to prevent duplicates
    existing_order = db.query(models.Order).filter_by(order_id_crm=order_in.order_id_crm).first()
    if existing_order:
        return existing_order

    db_order = models.Order(
        order_id_crm=order_in.order_id_crm,
        timestamp=order_in.timestamp,
        total_amount=order_in.total_amount,
        payment_method=order_in.payment_method
    )
    db.add(db_order)
    db.flush()  # Populates db_order.id

    for item in order_in.items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            item_name=item.item_name,
            category=item.category,
            price=item.price,
            quantity=item.quantity,
            total_price=item.total_price
        )
        db.add(db_item)
    
    return db_order


# --- Analytics & ML CRUD ---

def get_orders_count(db: Session) -> int:
    return db.query(models.Order).count()


def get_items_count(db: Session) -> int:
    return db.query(models.OrderItem).count()


def get_menu_analysis(db: Session) -> List[models.MenuAnalysis]:
    return db.query(models.MenuAnalysis).all()


def get_demand_forecast(db: Session) -> List[models.DemandForecast]:
    return db.query(models.DemandForecast).order_by(models.DemandForecast.date.asc()).all()


def update_menu_analysis(db: Session, analyses_data: List[Dict[str, Any]]) -> None:
    """Replace all menu analysis records with new ones in a single transaction."""
    # Delete all existing records
    db.execute(delete(models.MenuAnalysis))
    
    # Bulk insert new ones
    for item in analyses_data:
        db_item = models.MenuAnalysis(
            item_name=item["item_name"],
            category=item.get("category"),
            popularity_sales=item["popularity_sales"],
            avg_margin=item["avg_margin"],
            total_revenue=item["total_revenue"],
            cluster_label=item["cluster_label"]
        )
        db.add(db_item)
    
    db.commit()


def update_demand_forecast(db: Session, forecast_data: List[Dict[str, Any]]) -> None:
    """Replace all demand forecast records with new ones in a single transaction."""
    db.execute(delete(models.DemandForecast))
    
    for day in forecast_data:
        db_day = models.DemandForecast(
            date=day["date"],
            predicted_revenue=day["predicted_revenue"],
            predicted_orders=day["predicted_orders"],
            lower_bound_revenue=day["lower_bound_revenue"],
            upper_bound_revenue=day["upper_bound_revenue"]
        )
        db.add(db_day)
        
    db.commit()
