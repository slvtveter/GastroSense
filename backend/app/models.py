from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id_crm = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=True)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String(150), index=True, nullable=False)
    category = Column(String(100), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")


class MenuAnalysis(Base):
    __tablename__ = "menu_analysis"

    item_name = Column(String(150), primary_key=True)
    category = Column(String(100), nullable=True)
    popularity_sales = Column(Integer, nullable=False)
    avg_margin = Column(Numeric(10, 2), nullable=False)
    total_revenue = Column(Numeric(10, 2), nullable=False)
    cluster_label = Column(String(50), nullable=False)  # Stars, Workhorses, Puzzles, Dogs
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DemandForecast(Base):
    __tablename__ = "demand_forecast"

    date = Column(Date, primary_key=True)
    predicted_revenue = Column(Numeric(12, 2), nullable=False)
    predicted_orders = Column(Integer, nullable=False)
    lower_bound_revenue = Column(Numeric(12, 2), nullable=False)
    upper_bound_revenue = Column(Numeric(12, 2), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
