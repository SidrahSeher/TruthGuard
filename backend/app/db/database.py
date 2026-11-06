from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# The database is one file: backend/data/truthguard.db
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "truthguard.db"

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Create the tables if they do not exist yet."""
    from app.db import models  # noqa: F401  (makes the tables known)
    Base.metadata.create_all(engine)