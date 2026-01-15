"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator

from .models import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/venue_newsletters")

# Create engine
# For Cloud SQL, use NullPool to avoid connection pool issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool if "cloudsql" in DATABASE_URL else None,
    echo=os.getenv("ENVIRONMENT") == "development",  # Log SQL in development
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def drop_db():
    """Drop all tables - USE WITH CAUTION!"""
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session

    Usage in FastAPI:
        @app.get("/newsletters")
        def get_newsletters(db: Session = Depends(get_db)):
            return db.query(Newsletter).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions in standalone scripts

    Usage:
        with get_db_context() as db:
            newsletter = db.query(Newsletter).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alembic migration support
def run_migrations():
    """Run database migrations using Alembic"""
    import alembic.config
    alembic_args = [
        '--raiseerr',
        'upgrade', 'head',
    ]
    alembic.config.main(argv=alembic_args)


if __name__ == "__main__":
    # Initialize database when run directly
    print(f"Connecting to: {DATABASE_URL}")
    init_db()
