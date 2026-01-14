from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config import settings
from models import Base

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_MIN_SIZE,
    max_overflow=settings.DB_POOL_MAX_SIZE - settings.DB_POOL_MIN_SIZE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.ENVIRONMENT == "development"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def init_default_roles():
    """Initialize default roles"""
    from models import Role
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        if not roles:
            default_roles = [
                Role(name="user", description="Regular user"),
                Role(name="admin", description="Administrator"),
                Role(name="moderator", description="Moderator")
            ]
            db.add_all(default_roles)
            db.commit()
    finally:
        db.close()
