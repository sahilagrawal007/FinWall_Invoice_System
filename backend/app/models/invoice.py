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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing billing documents"""

    __tablename__ = "invoices"

    # Foreign Keys
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Invoice Information
    invoice_number = Column(String(50), nullable=False, index=True)
    status = Column(
        String(20), nullable=False, default="DRAFT"
    )  # DRAFT, SENT, VIEWED, PARTIALLY_PAID, PAID, OVERDUE, VOID

    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    # Financial Totals
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    tax_total = Column(Numeric(15, 2), nullable=False, default=0)
    total = Column(Numeric(15, 2), nullable=False, default=0)
    amount_paid = Column(Numeric(15, 2), nullable=False, default=0)
    balance_due = Column(Numeric(15, 2), nullable=False, default=0)

    # Additional Information
    currency_code = Column(String(3), default="INR", nullable=False)
    payment_terms_days = Column(Integer, default=30, nullable=False)
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)

    # Status Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization", backref="invoices")
    customer = relationship("Customer", backref="invoices")
    creator = relationship("User", backref="created_invoices")
    items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - ₹{self.total}>"


class InvoiceItem(Base, TimestampMixin):
    """Invoice line items"""

    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )  # Reference to catalog
    tax_id = Column(
        UUID(as_uuid=True), ForeignKey("taxes.id", ondelete="SET NULL"), nullable=True
    )

    # Line Item Data (Snapshot at time of invoice)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    rate = Column(Numeric(15, 2), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)  # quantity * rate

    # Tax Data (Snapshot)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)

    # Total
    total = Column(Numeric(15, 2), nullable=False)  # amount + tax_amount

    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    item = relationship("Item")
    tax = relationship("Tax")

    def __repr__(self):
        return f"<InvoiceItem {self.description} - ₹{self.total}>"
