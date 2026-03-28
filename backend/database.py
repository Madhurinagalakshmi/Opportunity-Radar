from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
 
# For Windows: Use SQLite (no PostgreSQL needed)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///opportunity_radar.db"  # Works on all platforms
)
 
# Create engine
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL (optional, for production)
    engine = create_engine(DATABASE_URL)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
    print(f"   Using: {DATABASE_URL}")
 
def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
# Run this file directly to initialize DB
if __name__ == "__main__":
    init_db()
    print("\n✅ You can now run: python main.py")