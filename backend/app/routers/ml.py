from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.upload import run_async_ml_training

router = APIRouter(prefix="/ml", tags=["ml"])

@router.post("/train")
def train_models(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger K-Means clustering and Time Series forecasting in the background."""
    background_tasks.add_task(run_async_ml_training, db)
    return {"success": True, "message": "ML training triggered in background."}
