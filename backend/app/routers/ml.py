from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.upload import run_async_ml_training
from app.ml.agent_manager import agent_manager

router = APIRouter(prefix="/ml", tags=["ml"])

class ChatRequest(BaseModel):
    message: str

@router.post("/train")
def train_models(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger K-Means clustering and Time Series forecasting in the background."""
    background_tasks.add_task(run_async_ml_training, db)
    return {"success": True, "message": "ML training triggered in background."}

@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """Pass query to the AgentManager."""
    reply = await agent_manager.process_query(request.message)
    return {"reply": reply}
