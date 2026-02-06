from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Item(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Item model representing products or services"""

    __tablename__ = "items"

    # Foreign Keys
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tax_id = Column(
        UUID(as_uuid=True), ForeignKey("taxes.id", ondelete="SET NULL"), nullable=True
    )  # Default tax

    # Item Information
    item_type = Column(
        String(20), nullable=False, default="SERVICE"
    )  # PRODUCT or SERVICE
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(100), nullable=True)  # Stock Keeping Unit
    unit = Column(
        String(50), default="unit", nullable=False
    )  # hour, piece, box, kg, etc.
    rate = Column(Numeric(15, 2), nullable=False)  # Current selling price

    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="items")
    tax = relationship("Tax", backref="items")

    def __repr__(self):
        return f"<Item {self.name} - ₹{self.rate}>"
