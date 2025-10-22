"""Session and engine management for AGER database."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from ..settings import get_db_path

_engines: dict[str, Engine] = {}


def init_db() -> None:
    """Initialize the database.

    Left empty - we use migrations to create tables.
    """
    pass


def get_engine(db_path: str | Path | None = None) -> Engine:
    """Get or create an engine for the given database path.

    Args:
        db_path: Path to the database file. If None, uses default from settings.

    Returns:
        SQLAlchemy Engine instance
    """
    if db_path is None:
        db_path = get_db_path()

    db_path_str = str(Path(db_path))

    if db_path_str not in _engines:
        _engines[db_path_str] = create_engine(f"sqlite:///{db_path_str}", echo=False)

    return _engines[db_path_str]


def get_session(db_path: str | Path | None = None) -> Session:
    """Get a new database session.

    Args:
        db_path: Path to the database file. If None, uses default from settings.

    Returns:
        A new SQLModel Session instance
    """
    engine = get_engine(db_path)
    return Session(engine)
