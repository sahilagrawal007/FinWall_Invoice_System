from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal
from app.schemas.tax import TaxListResponse


class ItemBase(BaseModel):
    """Base item schema"""

    item_type: str = Field(default="SERVICE", pattern="^(PRODUCT|SERVICE)$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    unit: str = Field(default="unit", max_length=50)
    rate: Decimal = Field(..., ge=0, description="Selling price")
    tax_id: Optional[UUID] = None
    is_active: bool = True


class ItemCreate(ItemBase):
    """Schema for creating an item"""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item (all fields optional)"""

    item_type: Optional[str] = Field(None, pattern="^(PRODUCT|SERVICE)$")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    rate: Optional[Decimal] = Field(None, ge=0)
    tax_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for item response"""

    id: UUID
    organization_id: UUID
    tax: Optional[TaxListResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """Minimal schema for item list"""

    id: UUID
    name: str
    item_type: str
    rate: Decimal
    unit: str
    sku: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
