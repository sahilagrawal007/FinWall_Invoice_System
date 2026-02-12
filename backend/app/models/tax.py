"""
Tax Model

Represents tax rates (GST, etc.).
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Tax(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Tax model representing tax rates (GST, etc.)"""

    __tablename__ = "taxes"

    # Foreign Key
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tax Information
    name = Column(String(100), nullable=False)  # e.g., "GST 18%", "GST 5%"
    rate = Column(Numeric(5, 2), nullable=False)  # e.g., 18.00 for 18%
    tax_type = Column(
        String(20), nullable=False, default="GST"
    )  # GST, IGST, CGST, SGST, CESS, NONE

    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="taxes")

    def __repr__(self):
        return f"<Tax {self.name} - {self.rate}%>"
