from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Customer(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Customer model representing businesses or individuals"""

    __tablename__ = "customers"

    # Foreign Key
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    customer_type = Column(
        String(20), nullable=False, default="BUSINESS"
    )  # BUSINESS or INDIVIDUAL
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    # Billing Address
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), default="India")

    # Shipping Address
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)

    # Tax and Payment Information
    tax_id = Column(String(50), nullable=True, comment="GST Number or PAN")
    currency_code = Column(String(3), default="INR", nullable=False)
    payment_terms_days = Column(Integer, default=30, nullable=False)

    # Additional Information
    credit_limit = Column(Numeric(15, 2), nullable=True)
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="customers")

    def __repr__(self):
        return f"<Customer {self.name}>"

    @property
    def billing_address(self):
        """Return formatted billing address"""
        parts = [
            self.billing_address_line1,
            self.billing_address_line2,
            self.billing_city,
            self.billing_state,
            self.billing_postal_code,
            self.billing_country,
        ]
        return ", ".join([p for p in parts if p])

    @property
    def shipping_address(self):
        """Return formatted shipping address, fallback to billing if not set"""
        if self.shipping_address_line1:
            parts = [
                self.shipping_address_line1,
                self.shipping_address_line2,
                self.shipping_city,
                self.shipping_state,
                self.shipping_postal_code,
                self.shipping_country,
            ]
            return ", ".join([p for p in parts if p])
        return self.billing_address
