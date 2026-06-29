import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import sys
import os

from sqlalchemy.pool import StaticPool

# Ensure the backend directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db
from app import models
from app.main import app


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def _disable_dense_retriever():
    """Keep tests hermetic and fast: force the RAG pipeline onto its TF-IDF-only
    fallback path so it never hits the live Gemini embeddings API (which would
    make tests depend on network access and free-tier quota). This also doubles
    as a regression check that retrieval degrades gracefully without embeddings.
    """
    from app.ml.embedding_retriever import embedding_retriever
    saved_available, saved_matrix = embedding_retriever.available, embedding_retriever._doc_matrix
    embedding_retriever.available = False
    embedding_retriever._doc_matrix = None
    yield
    embedding_retriever.available, embedding_retriever._doc_matrix = saved_available, saved_matrix


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session():
    """Create all tables in the SQLite database and yield a clean session per test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client", scope="function")
def fixture_client(db_session, monkeypatch):
    """Override get_db dependency in the FastAPI application and yield a test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # The seed-demo background task trains models off the request path using its
    # own SessionLocal(). Point that at the same in-memory test session so the
    # background work lands in the test DB (the TestClient runs background tasks
    # synchronously during the request), letting us assert on its results.
    import app.routers.upload as upload_module
    monkeypatch.setattr(upload_module, "SessionLocal", lambda: db_session)

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
