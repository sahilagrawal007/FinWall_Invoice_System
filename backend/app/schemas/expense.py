from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class ExpenseBase(BaseModel):
    """Base expense schema"""

    vendor_name: str = Field(..., min_length=1, max_length=255)
    expense_date: date
    category: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_method: str = Field(
        ..., pattern="^(CASH|BANK_TRANSFER|CREDIT_CARD|DEBIT_CARD|CHEQUE|UPI|ONLINE)$"
    )
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    receipt_url: Optional[str] = Field(None, max_length=500)
    is_billable: bool = False
    customer_id: Optional[UUID] = None


class ExpenseCreate(ExpenseBase):
    """Schema for creating expense"""

    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating expense"""

    vendor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    expense_date: Optional[date] = None
    category: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = Field(
        None, pattern="^(CASH|BANK_TRANSFER|CREDIT_CARD|DEBIT_CARD|CHEQUE|UPI|ONLINE)$"
    )
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    receipt_url: Optional[str] = Field(None, max_length=500)
    is_billable: Optional[bool] = None
    customer_id: Optional[UUID] = None


class ExpenseResponse(ExpenseBase):
    """Schema for expense response"""

    id: UUID
    organization_id: UUID
    expense_number: str
    total: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    """Minimal schema for expense list"""

    id: UUID
    expense_number: str
    vendor_name: str
    expense_date: date
    category: Optional[str]
    total: Decimal
    payment_method: str
    is_billable: bool
    created_at: datetime

    class Config:
        from_attributes = True
