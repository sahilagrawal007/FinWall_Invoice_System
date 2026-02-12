"""
Base Model Mixins

Provides reusable mixins for common model patterns.
Uses CHAR(36) for UUID storage to support MySQL.
"""

from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.sql import func
import uuid


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """
    Mixin for UUID primary key.
    Uses CHAR(36) for MySQL compatibility instead of PostgreSQL UUID type.
    """

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    is_deleted = Column(Boolean, default=False, nullable=False)