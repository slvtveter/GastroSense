import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models

def test_read_root(client: TestClient):
    """Test that the API root endpoint is reachable and reports online status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_upload_csv(client: TestClient, db_session: Session):
    """Test uploading a raw CRM receipt CSV file with Russian headers.
    Verifies column mapping, Pydantic validation, and DB persistence.
    """
    # Create a mock CSV content with typical Russian headers
    csv_data = (
        "ID чека,дата,номенклатура,цена,количество,категория\n"
        "TB-1001,2026-06-01 12:30:00,Бургер True,450.0,1,Burgers\n"
        "TB-1001,2026-06-01 12:30:00,Картофель фри,180.0,2,Sides\n"
        "TB-1002,2026-06-01 13:15:00,Кока-кола,120.0,1,Drinks\n"
    )
    
    # Pack into bytes buffer
    file_bytes = csv_data.encode("utf-8")
    
    # Send POST request
    response = client.post(
        "/api/v1/upload/checks",
        files={"file": ("test_checks.csv", file_bytes, "text/csv")}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["orders_processed"] == 2
    assert data["items_processed"] == 3
    assert len(data["errors"]) == 0
    
    # Verify database state
    orders = db_session.query(models.Order).all()
    assert len(orders) == 2
    
    order1 = db_session.query(models.Order).filter_by(order_id_crm="TB-1001").first()
    assert order1 is not None
    assert float(order1.total_amount) == 450.0 * 1 + 180.0 * 2
    assert len(order1.items) == 2
    
    order2 = db_session.query(models.Order).filter_by(order_id_crm="TB-1002").first()
    assert order2 is not None
    assert float(order2.total_amount) == 120.0

def test_seed_demo_and_analytics(client: TestClient, db_session: Session):
    """Test database seeding and subsequent analytics queries.
    Verifies that seeding triggers background ML training, which populates
    menu engineering and time series forecast tables in SQLite.
    """
    # 1. Trigger demo seeding
    seed_response = client.post("/api/v1/upload/seed-demo")
    assert seed_response.status_code == 200
    seed_data = seed_response.json()
    assert seed_data["success"] is True
    assert seed_data["orders_seeded"] > 0
    assert seed_data["items_seeded"] > 0
    
    # 2. Check stats endpoint
    stats_response = client.get("/api/v1/analytics/stats")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["total_orders"] == seed_data["orders_seeded"]
    assert stats_data["total_revenue"] > 0
    assert stats_data["avg_check"] > 0
    
    # 3. Check history endpoint
    hist_response = client.get("/api/v1/analytics/history?days=30")
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert len(hist_data) > 0
    assert "revenue" in hist_data[0]
    assert "orders_count" in hist_data[0]
    
    # 4. Check Menu Engineering (K-Means) output
    menu_response = client.get("/api/v1/analytics/menu")
    assert menu_response.status_code == 200
    menu_data = menu_response.json()
    assert len(menu_data) > 0
    # Check that K-Means successfully assigned quadrant labels
    assert "cluster_label" in menu_data[0]
    assert menu_data[0]["cluster_label"] in ["Stars", "Workhorses", "Puzzles", "Dogs"]
    
    # 5. Check Demand Forecast (LightGBM) output
    fore_response = client.get("/api/v1/analytics/forecast")
    assert fore_response.status_code == 200
    fore_data = fore_response.json()
    assert len(fore_data) == 7  # Exactly 7 days forecasted
    assert "predicted_revenue" in fore_data[0]
    assert "lower_bound_revenue" in fore_data[0]
    assert "upper_bound_revenue" in fore_data[0]
    
    # 6. Check Market Basket associations heatmap data
    assoc_response = client.get("/api/v1/analytics/associations")
    assert assoc_response.status_code == 200
    assoc_data = assoc_response.json()
    assert "index" in assoc_data
    assert "data" in assoc_data
    assert len(assoc_data["index"]) > 0
    # Probabilities should be between 0 and 1
    assert 0.0 <= assoc_data["data"][0][0] <= 1.0
