from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.schemas.customer import CustomerListResponse


# Invoice Item Schemas
class InvoiceItemBase(BaseModel):
    """Base invoice item schema"""

    item_id: Optional[UUID] = None
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    rate: Decimal = Field(..., ge=0)
    tax_id: Optional[UUID] = None


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating invoice item"""

    pass


class InvoiceItemResponse(BaseModel):
    """Schema for invoice item response"""

    id: int
    item_id: Optional[UUID]
    description: str
    quantity: Decimal
    rate: Decimal
    amount: Decimal
    tax_id: Optional[UUID]
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    sort_order: int

    class Config:
        from_attributes = True


# Invoice Schemas
class InvoiceBase(BaseModel):
    """Base invoice schema"""

    customer_id: UUID
    invoice_date: date
    due_date: date
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice"""

    items: List[InvoiceItemCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice (only DRAFT invoices)"""

    customer_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    customer: Optional[CustomerListResponse] = None
    invoice_number: str
    status: str
    invoice_date: date
    due_date: date
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    currency_code: str
    payment_terms_days: int
    notes: Optional[str]
    internal_notes: Optional[str]
    terms_and_conditions: Optional[str]
    items: List[InvoiceItemResponse]
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    paid_at: Optional[datetime]
    voided_at: Optional[datetime]
    void_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Minimal schema for invoice list"""

    id: UUID
    invoice_number: str
    customer_id: UUID
    customer: Optional[CustomerListResponse] = None
    status: str
    invoice_date: date
    due_date: date
    total: Decimal
    balance_due: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceVoidRequest(BaseModel):
    """Schema for voiding invoice"""

    reason: str = Field(..., min_length=1, max_length=500)
