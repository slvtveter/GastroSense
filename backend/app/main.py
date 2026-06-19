from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.database import engine, Base, SessionLocal
from app.routers import upload, analytics, ml, export
from app.config import settings
from app.ml.rag_engine import rag_engine

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Try to create tables, but don't hang if DB is down
    try:
        print("Connecting to database...")
        Base.metadata.create_all(bind=engine)
        print("Database connected and tables verified.")
        with SessionLocal() as db:
            rag_engine.refresh_from_db(db)
        # Self-heal: if the (ephemeral) DB came up empty after a cold start,
        # auto-seed it in the background so the dashboard always has data.
        from app.routers.upload import ensure_seeded_on_startup
        ensure_seeded_on_startup()
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")
        print("Starting in 'No-DB' mode (some features will be disabled).")
    yield
    # Shutdown: Clean up or close connections if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set CORS origins to allow local development dashboard to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(ml.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs"
    }
