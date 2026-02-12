"""
Quote Model

Represents estimates/proposals sent to customers.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    Numeric,
    Date,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Quote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Quote model representing estimates/proposals"""

    __tablename__ = "quotes"

    # Foreign Keys
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        String(36),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Quote Information
    quote_number = Column(String(50), nullable=False, index=True)
    status = Column(
        String(20), nullable=False, default="DRAFT"
    )  # DRAFT, SENT, VIEWED, ACCEPTED, REJECTED, EXPIRED, CONVERTED

    # Dates
    quote_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)

    # Financial Totals
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_total = Column(Numeric(15, 2), nullable=False, default=0)
    total = Column(Numeric(15, 2), nullable=False, default=0)

    # Additional Information
    currency_code = Column(String(3), default="INR", nullable=False)
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)

    # Status Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)

    # Conversion
    converted_invoice_id = Column(
        String(36),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization = relationship("Organization", backref="quotes")
    customer = relationship("Customer", backref="quotes")
    creator = relationship("User", backref="created_quotes")
    converted_invoice = relationship("Invoice", backref="source_quote")
    items = relationship(
        "QuoteItem", back_populates="quote", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Quote {self.quote_number} - ₹{self.total}>"


class QuoteItem(Base, TimestampMixin):
    """Quote line items"""

    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    quote_id = Column(
        String(36),
        ForeignKey("quotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(
        String(36), ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    tax_id = Column(
        String(36), ForeignKey("taxes.id", ondelete="SET NULL"), nullable=True
    )

    # Line Item Data (Snapshot)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    rate = Column(Numeric(15, 2), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)

    # Tax Data (Snapshot)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)

    # Total
    total = Column(Numeric(15, 2), nullable=False)

    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    quote = relationship("Quote", back_populates="items")
    item = relationship("Item")
    tax = relationship("Tax")

    def __repr__(self):
        return f"<QuoteItem {self.description} - ₹{self.total}>"
