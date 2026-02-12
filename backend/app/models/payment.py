"""
Payment Model

Represents payments received from customers.
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Numeric,
    Date,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Payment(Base, UUIDMixin, TimestampMixin):
    """Payment model representing money received from customers"""

    __tablename__ = "payments"

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
    invoice_id = Column(
        String(36),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Payment Information
    payment_number = Column(String(50), nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)

    # Payment Method
    payment_method = Column(
        String(20), nullable=False
    )  # CASH, BANK_TRANSFER, UPI, CHEQUE, CREDIT_CARD, DEBIT_CARD, ONLINE
    reference_number = Column(
        String(100), nullable=True
    )  # UTR, Cheque no, Transaction ID
    notes = Column(Text, nullable=True)

    # Gateway Integration Fields (for future use)
    gateway_name = Column(String(50), nullable=True)  # razorpay, stripe, etc.
    gateway_payment_id = Column(String(100), nullable=True)  # External payment ID
    gateway_order_id = Column(String(100), nullable=True)  # External order ID
    gateway_response = Column(
        Text, nullable=True
    )  # Store full gateway response as JSON

    # Void Management
    is_voided = Column(Boolean, default=False, nullable=False)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(Text, nullable=True)
    voided_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    organization = relationship("Organization", backref="payments")
    customer = relationship("Customer", backref="payments")
    invoice = relationship("Invoice", backref="payments")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_payments"
    )
    voider = relationship("User", foreign_keys=[voided_by], backref="voided_payments")

    def __repr__(self):
        return f"<Payment {self.payment_number} - ₹{self.amount}>"
