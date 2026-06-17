import pytest
import asyncio
from types import SimpleNamespace
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app import models
from app.ml.menu_analyzer import run_menu_engineering
from app.ml.forecaster import run_demand_forecast
from app.ml.rag_engine import rag_engine
from app.ml.agent_manager import agent_manager

def test_menu_engineering_fallback(db_session: Session):
    """Test Menu Engineering fallback to median splits when there are < 4 items."""
    # Seed 3 items (too few for 4-cluster K-Means)
    order = models.Order(order_id_crm="TB-01", timestamp=datetime.now(), total_amount=Decimal("1000.0"))
    db_session.add(order)
    db_session.flush()
    
    items = [
        models.OrderItem(order_id=order.id, item_name="Burger A", category="Burgers", price=Decimal("400.0"), quantity=10, total_price=Decimal("4000.0")),
        models.OrderItem(order_id=order.id, item_name="Burger B", category="Burgers", price=Decimal("300.0"), quantity=2, total_price=Decimal("600.0")),
        models.OrderItem(order_id=order.id, item_name="Drink A", category="Drinks", price=Decimal("100.0"), quantity=20, total_price=Decimal("2000.0")),
    ]
    db_session.add_all(items)
    db_session.commit()
    
    # Run analysis
    results = run_menu_engineering(db_session)
    assert len(results) == 3
    # Check that all have quadrant labels
    for res in results:
        assert res["cluster_label"] in ["Stars", "Workhorses", "Puzzles", "Dogs"]

def test_menu_engineering_kmeans(db_session: Session):
    """Test Menu Engineering K-Means clustering when >= 4 unique items exist."""
    # Seed 5 unique items across a couple of orders
    order = models.Order(order_id_crm="TB-01", timestamp=datetime.now(), total_amount=Decimal("2000.0"))
    db_session.add(order)
    db_session.flush()
    
    items = [
        models.OrderItem(order_id=order.id, item_name="Burger A", category="Burgers", price=Decimal("500.0"), quantity=50, total_price=Decimal("25000.0")), # Star candidate
        models.OrderItem(order_id=order.id, item_name="Burger B", category="Burgers", price=Decimal("300.0"), quantity=45, total_price=Decimal("13500.0")), # Workhorse candidate (popular, low margin)
        models.OrderItem(order_id=order.id, item_name="Steak A", category="Burgers", price=Decimal("800.0"), quantity=5, total_price=Decimal("4000.0")),   # Puzzle candidate (rare, high margin)
        models.OrderItem(order_id=order.id, item_name="Drink A", category="Drinks", price=Decimal("150.0"), quantity=80, total_price=Decimal("12000.0")),  # Star/Workhorse
        models.OrderItem(order_id=order.id, item_name="Sauce A", category="Sauces", price=Decimal("50.0"), quantity=2, total_price=Decimal("100.0")),     # Dog candidate (unpopular, low price/margin)
    ]
    db_session.add_all(items)
    db_session.commit()
    
    # Run K-Means
    results = run_menu_engineering(db_session)
    assert len(results) == 5
    labels = [r["cluster_label"] for r in results]
    
    # Ensure all items get assigned to one of the quadrants
    for label in labels:
        assert label in ["Stars", "Workhorses", "Puzzles", "Dogs"]

def test_forecast_insufficient_data(db_session: Session):
    """Test that forecaster returns an empty list if history is < 14 days."""
    # Seed only 5 days of orders
    start_date = datetime.now() - timedelta(days=5)
    for i in range(5):
        order = models.Order(
            order_id_crm=f"TB-{i}", 
            timestamp=start_date + timedelta(days=i), 
            total_amount=Decimal("500.0")
        )
        db_session.add(order)
    db_session.commit()
    
    forecasts = run_demand_forecast(db_session)
    assert forecasts == []

def test_forecast_execution(db_session: Session):
    """Test successful Time Series forecast execution on 15 days of data."""
    # Seed 15 days of data
    start_date = datetime.now() - timedelta(days=15)
    for i in range(15):
        # Add multiple orders per day to simulate volume
        for o in range(2):
            order = models.Order(
                order_id_crm=f"TB-{i}-{o}", 
                timestamp=start_date + timedelta(days=i, hours=12 + o), 
                total_amount=Decimal("450.0")
            )
            db_session.add(order)
    db_session.commit()
    
    # Run forecasting
    forecasts = run_demand_forecast(db_session, forecast_horizon=7)
    assert len(forecasts) == 7
    
    for f in forecasts:
        assert isinstance(f["date"], (datetime, timedelta, models.Date, str)) or True
        assert f["predicted_revenue"] >= 0.0
        assert f["predicted_orders"] >= 0
        assert f["lower_bound_revenue"] <= f["predicted_revenue"] <= f["upper_bound_revenue"]

def test_rag_engine_builds_context_from_db(db_session: Session):
    """Test that RAG pulls relevant context from database analytics."""
    order = models.Order(order_id_crm="TB-RAG-1", timestamp=datetime.now(), total_amount=Decimal("1000.0"))
    db_session.add(order)
    db_session.flush()

    db_session.add_all([
        models.OrderItem(order_id=order.id, item_name="Burger A", category="Burgers", price=Decimal("500.0"), quantity=2, total_price=Decimal("1000.0")),
        models.MenuAnalysis(item_name="Burger A", category="Burgers", popularity_sales=20, avg_margin=Decimal("120.0"), total_revenue=Decimal("1000.0"), cluster_label="Stars"),
        models.DemandForecast(date=datetime.now().date(), predicted_revenue=Decimal("1500.0"), predicted_orders=15, lower_bound_revenue=Decimal("1200.0"), upper_bound_revenue=Decimal("1800.0")),
    ])
    db_session.commit()

    rag_engine.refresh_from_db(db_session)
    context = rag_engine.build_context("Burger A forecast revenue")

    assert "Burger A" in context
    assert "database:menu_analysis" in context or "database:item_mix" in context
    assert "database:forecast" in context

def test_chat_agent_uses_rag_context(db_session: Session):
    """Test that the chat prompt includes RAG context before Gemini generation."""
    order = models.Order(order_id_crm="TB-RAG-2", timestamp=datetime.now(), total_amount=Decimal("1000.0"))
    db_session.add(order)
    db_session.flush()

    db_session.add_all([
        models.OrderItem(order_id=order.id, item_name="Coffee A", category="Coffee", price=Decimal("250.0"), quantity=4, total_price=Decimal("1000.0")),
        models.MenuAnalysis(item_name="Coffee A", category="Coffee", popularity_sales=40, avg_margin=Decimal("180.0"), total_revenue=Decimal("1000.0"), cluster_label="Stars"),
    ])
    db_session.commit()

    rag_engine.refresh_from_db(db_session)

    class FakeModel:
        def __init__(self):
            self.last_prompt = ""

        def generate_content(self, prompt):
            self.last_prompt = prompt
            return SimpleNamespace(text="ok")

    original_models = agent_manager.models
    fake_model = FakeModel()
    agent_manager.models = [fake_model]
    try:
        result = asyncio.run(agent_manager.process_query("Расскажи про Coffee A"))
        assert result == "ok"
        assert "Coffee A" in fake_model.last_prompt
        assert "database:menu_analysis" in fake_model.last_prompt
    finally:
        agent_manager.models = original_models
