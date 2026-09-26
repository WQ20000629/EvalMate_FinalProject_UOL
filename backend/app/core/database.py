# ------------------------------------------------------------------
# File: backend/app/core/database.py
# Purpose: Sets up the database connection, SQLAlchemy base, and request sessions.
# ------------------------------------------------------------------

# Import the libraries needed for database setup
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Load the database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env")

# Create the database engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Create a database session for each request and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
