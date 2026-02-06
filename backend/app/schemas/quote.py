from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.schemas.customer import CustomerListResponse


# Quote Item Schemas
class QuoteItemBase(BaseModel):
    """Base quote item schema"""

    item_id: Optional[UUID] = None
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    rate: Decimal = Field(..., ge=0)
    tax_id: Optional[UUID] = None


class QuoteItemCreate(QuoteItemBase):
    """Schema for creating quote item"""

    pass


class QuoteItemResponse(BaseModel):
    """Schema for quote item response"""

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


# Quote Schemas
class QuoteBase(BaseModel):
    """Base quote schema"""

    customer_id: UUID
    quote_date: date
    expiry_date: date
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class QuoteCreate(QuoteBase):
    """Schema for creating quote"""

    items: List[QuoteItemCreate] = Field(..., min_length=1)


class QuoteUpdate(BaseModel):
    """Schema for updating quote (only DRAFT quotes)"""

    customer_id: Optional[UUID] = None
    quote_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    items: Optional[List[QuoteItemCreate]] = None


class QuoteResponse(BaseModel):
    """Schema for quote response"""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    customer: Optional[CustomerListResponse] = None
    quote_number: str
    status: str
    quote_date: date
    expiry_date: date
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    currency_code: str
    notes: Optional[str]
    terms_and_conditions: Optional[str]
    items: List[QuoteItemResponse]
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    converted_at: Optional[datetime]
    converted_invoice_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteListResponse(BaseModel):
    """Minimal schema for quote list"""

    id: UUID
    quote_number: str
    customer_id: UUID
    customer: Optional[CustomerListResponse] = None
    status: str
    quote_date: date
    expiry_date: date
    total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteAcceptRequest(BaseModel):
    """Schema for accepting quote"""

    notes: Optional[str] = Field(None, max_length=500)


class QuoteRejectRequest(BaseModel):
    """Schema for rejecting quote"""

    reason: str = Field(..., min_length=1, max_length=500)
