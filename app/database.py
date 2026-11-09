import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
    Session
)
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://fastapi_user:fastapi_password@localhost:5432/fastapi_db"
)

# Database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Base class for ORM models
class Base(DeclarativeBase):
    pass


# Database session dependency
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# Database health check
def check_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.scalar() == 1

    except SQLAlchemyError:
        return False