from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

# --- Order Item Schemas ---
class OrderItemBase(BaseModel):
    item_name: str = Field(..., max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    price: Decimal
    quantity: int
    total_price: Decimal

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    class Config:
        from_attributes = True


# --- Order/Receipt Schemas ---
class OrderBase(BaseModel):
    order_id_crm: str = Field(..., max_length=100)
    timestamp: datetime
    total_amount: Decimal
    payment_method: Optional[str] = Field(None, max_length=50)

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderResponse(OrderBase):
    id: int
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


# --- Menu Analysis Schemas ---
class MenuAnalysisResponse(BaseModel):
    item_name: str
    category: Optional[str] = None
    popularity_sales: int
    avg_margin: Decimal
    total_revenue: Decimal
    cluster_label: str
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Demand Forecast Schemas ---
class DemandForecastResponse(BaseModel):
    date: date
    predicted_revenue: Decimal
    predicted_orders: int
    lower_bound_revenue: Decimal
    upper_bound_revenue: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Utility API Schemas ---
class UploadStatus(BaseModel):
    success: bool
    message: str
    orders_processed: int
    items_processed: int
    errors: List[str] = []
