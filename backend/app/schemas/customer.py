from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal


class CustomerBase(BaseModel):
    """Base customer schema"""

    customer_type: str = Field(default="BUSINESS", pattern="^(BUSINESS|INDIVIDUAL)$")
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)

    # Billing Address
    billing_address_line1: Optional[str] = Field(None, max_length=255)
    billing_address_line2: Optional[str] = Field(None, max_length=255)
    billing_city: Optional[str] = Field(None, max_length=100)
    billing_state: Optional[str] = Field(None, max_length=100)
    billing_postal_code: Optional[str] = Field(None, max_length=20)
    billing_country: str = Field(default="India", max_length=100)

    # Shipping Address
    shipping_address_line1: Optional[str] = Field(None, max_length=255)
    shipping_address_line2: Optional[str] = Field(None, max_length=255)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_postal_code: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=100)

    # Tax and Payment
    tax_id: Optional[str] = Field(None, max_length=50)
    currency_code: str = Field(default="INR", max_length=3)
    payment_terms_days: int = Field(default=30, ge=0, le=365)

    # Additional
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""

    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer (all fields optional)"""

    customer_type: Optional[str] = Field(None, pattern="^(BUSINESS|INDIVIDUAL)$")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)

    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None

    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None

    tax_id: Optional[str] = None
    currency_code: Optional[str] = None
    payment_terms_days: Optional[int] = Field(None, ge=0, le=365)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response"""

    id: UUID
    organization_id: UUID
    billing_address: str
    shipping_address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Minimal schema for customer list"""

    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    customer_type: str
    billing_city: Optional[str]
    billing_state: Optional[str]
    payment_terms_days: int
    is_active: bool

    class Config:
        from_attributes = True
