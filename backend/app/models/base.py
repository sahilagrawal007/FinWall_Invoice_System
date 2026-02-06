from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
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
    """Mixin for UUID primary key"""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    is_deleted = Column(Boolean, default=False, nullable=False)