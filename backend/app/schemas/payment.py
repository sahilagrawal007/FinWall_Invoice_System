from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class PaymentBase(BaseModel):
    """Base payment schema"""

    invoice_id: UUID
    payment_date: date
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(
        ..., pattern="^(CASH|BANK_TRANSFER|UPI|CHEQUE|CREDIT_CARD|DEBIT_CARD|ONLINE)$"
    )
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating payment (manual)"""

    pass


class PaymentGatewayCreate(BaseModel):
    """Schema for creating payment via gateway (future use)"""

    invoice_id: UUID
    amount: Decimal = Field(..., gt=0)
    gateway_name: str  # razorpay, stripe
    gateway_payment_id: str
    gateway_order_id: Optional[str] = None
    gateway_response: Optional[str] = None  # JSON string


class PaymentResponse(BaseModel):
    """Schema for payment response"""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    invoice_id: Optional[UUID]
    payment_number: str
    payment_date: date
    amount: Decimal
    payment_method: str
    reference_number: Optional[str]
    notes: Optional[str]

    # Gateway fields (will be null for manual payments)
    gateway_name: Optional[str]
    gateway_payment_id: Optional[str]
    gateway_order_id: Optional[str]

    is_voided: bool
    voided_at: Optional[datetime]
    void_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Minimal schema for payment list"""

    id: UUID
    payment_number: str
    payment_date: date
    amount: Decimal
    payment_method: str
    reference_number: Optional[str]
    is_voided: bool

    class Config:
        from_attributes = True


class PaymentVoidRequest(BaseModel):
    """Schema for voiding payment"""

    reason: str = Field(..., min_length=1, max_length=500)
