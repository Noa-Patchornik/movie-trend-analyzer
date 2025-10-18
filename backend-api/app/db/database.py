import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection details are loaded from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "trend_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "strong_password")
DB_PORT = os.getenv("DB_PORT", "5432")

# Construct the full PostgreSQL connection URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create the SQLAlchemy Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
    # We add an optional isolation level, useful for concurrent environments
    # connect_args={"options": "-c timezone=utc"}
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for our declarative models
Base = declarative_base()

# Dependency to get a DB session (used by FastAPI endpoints)
def get_db():
    """Provides a transactional database session for FastAPI requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()