"""SQLAlchemy database models and connection for KERN."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

import logging
logger = logging.getLogger(__name__)

Base = declarative_base()

# ─── Models ─────────────────────────────────────────────────────────────────

class Upload(Base):
    """Track every file upload."""
    __tablename__ = "uploads"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    row_count = Column(Integer, nullable=False)
    product_count = Column(Integer, nullable=False)
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    has_dates = Column(Boolean, default=False)
    currency = Column(String(10), default="$")
    data_hash = Column(String(64), nullable=True)  # SHA-256 for deduplication
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)  # When session expires (2 hours later)
    gross_margin = Column(Float, nullable=True)  # User-provided margin (0.65 = 65%)
    margin_source = Column(String(20), default="estimated")  # "estimated" or "provided"
    has_cost_data = Column(Boolean, default=False)  # CSV has cost column?
    cost_column_name = Column(String(100), nullable=True)  # e.g., "cost", "cogs"


class DBSession(Base):
    """Track active sessions (mirrors Redis, for audit + recovery)."""
    __tablename__ = "db_sessions"

    id = Column(String(36), primary_key=True)  # UUID = session_id
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    upload_id = Column(String(36), nullable=True)  # FK to uploads.id


class Dismissal(Base):
    """Track dismissed recommendations for feedback loop."""
    __tablename__ = "dismissals"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), nullable=False, index=True)
    upload_id = Column(String(36), nullable=False, index=True)
    rec_id = Column(String(255), nullable=False)  # e.g., "pricing_raise_product_1"
    rec_type = Column(String(50), nullable=True)  # e.g., "pricing", "bundle", "declining"
    dismissed_at = Column(DateTime, default=datetime.utcnow, index=True)
    reason = Column(Text, nullable=True)  # User feedback (if provided)


# ─── Migrations ─────────────────────────────────────────────────────────────

def _run_migrations(engine) -> None:
    """Add new columns to existing tables without breaking existing deployments."""
    migrations = [
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS gross_margin FLOAT",
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS margin_source VARCHAR(20) DEFAULT 'estimated'",
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS has_cost_data BOOLEAN DEFAULT FALSE",
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS cost_column_name VARCHAR(100)",
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                logger.debug(f"Migration skipped (likely already applied): {e}")
        conn.commit()


# ─── Connection Pool ────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL")
_engine = None
_session_factory = None
_db_available = False

def init_db():
    """Initialize database connection. Call once at app startup."""
    global _engine, _session_factory, _db_available

    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set. Database features disabled.")
        _db_available = False
        return

    try:
        _engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}
        )

        # Test connection
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Create tables
        Base.metadata.create_all(_engine)

        # Idempotent migrations: add new columns if they don't exist
        _run_migrations(_engine)

        _session_factory = sessionmaker(bind=_engine)
        _db_available = True
        logger.info("PostgreSQL connected and tables initialized.")

    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Database logging disabled.")
        _db_available = False


def get_db_session() -> Optional[Session]:
    """Get a SQLAlchemy session. Returns None if DB unavailable."""
    if not _db_available or _session_factory is None:
        return None
    try:
        return _session_factory()
    except Exception as e:
        logger.warning(f"Failed to get DB session: {e}")
        return None


def is_db_available() -> bool:
    """Check if database is connected."""
    return _db_available
