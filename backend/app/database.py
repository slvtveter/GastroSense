from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# For SQLite, we need connect_args={"check_same_thread": False}
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
    # Removed pool_size/max_overflow as they conflict with SQLite default settings
)

# SQLite concurrency tuning. The dashboard polls several read endpoints every
# few seconds WHILE a background task seeds a long history in big chunked
# transactions (preset switch / cold-start auto-seed). Default SQLite (rollback
# journal + busy_timeout=0) makes those concurrent reads fail instantly with
# "database is locked" the moment a write is in flight - which the frontend then
# renders as a stuck "Loading…" dashboard. WAL lets readers keep serving the
# last committed snapshot while a writer runs; busy_timeout makes any genuinely
# contended statement wait instead of erroring; synchronous=NORMAL is the
# WAL-recommended durability level and keeps the bulk seed fast.
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
