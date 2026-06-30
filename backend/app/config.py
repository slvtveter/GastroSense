import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env as early as possible. app.config is imported (via app.database) before
# any module that reads environment variables at import time - notably
# app.ml.embedding_retriever, whose constructor checks GEMINI_API_KEY. If .env is
# only loaded later (it used to be loaded in main.py, *after* the import block),
# that constructor has already run with no key, so dense Gemini embeddings stay
# silently disabled and the RAG chat degrades to TF-IDF-only (which is blind to
# Russian queries). Loading here guarantees the key is in os.environ in time.
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


class Settings:
    PROJECT_NAME: str = "GastroSense Analytics"
    API_V1_STR: str = "/api/v1"
    
    # Use SQLite by default for easy portfolio running without a DB server
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./analytics.db"
    )

settings = Settings()
