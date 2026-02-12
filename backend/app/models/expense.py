"""
Expense Model

Represents business expenses.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, Date, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Expense(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Expense model representing business expenses"""

    __tablename__ = "expenses"

    # Foreign Keys
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        String(36),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # If billable
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Expense Information
    expense_number = Column(String(50), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    expense_date = Column(Date, nullable=False)
    category = Column(
        String(100), nullable=True
    )  # Office Supplies, Travel, Utilities, etc.

    # Financial Information
    amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    total = Column(Numeric(15, 2), nullable=False)

    # Payment Information
    payment_method = Column(
        String(20), nullable=False
    )  # CASH, BANK_TRANSFER, CREDIT_CARD, etc.
    reference_number = Column(
        String(100), nullable=True
    )  # Receipt number, invoice number

    # Additional Information
    description = Column(Text, nullable=True)
    receipt_url = Column(String(500), nullable=True)  # Link to uploaded receipt

    # Billable
    is_billable = Column(Boolean, default=False, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="expenses")
    customer = relationship("Customer", backref="billable_expenses")
    creator = relationship("User", backref="created_expenses")

    def __repr__(self):
        return f"<Expense {self.expense_number} - {self.vendor_name} - ₹{self.total}>"
