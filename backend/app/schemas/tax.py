from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TaxBase(BaseModel):
    """Base tax schema"""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Tax name (e.g., GST 18%)"
    )
    rate: Decimal = Field(
        ..., ge=0, le=100, description="Tax rate percentage (e.g., 18.00)"
    )
    tax_type: str = Field(default="GST", pattern="^(GST|IGST|CGST|SGST|CESS|NONE)$")
    is_active: bool = True


class TaxCreate(TaxBase):
    """Schema for creating a tax"""

    pass


class TaxUpdate(BaseModel):
    """Schema for updating a tax (all fields optional)"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_type: Optional[str] = Field(None, pattern="^(GST|IGST|CGST|SGST|CESS|NONE)$")
    is_active: Optional[bool] = None


class TaxResponse(TaxBase):
    """Schema for tax response"""

    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaxListResponse(BaseModel):
    """Minimal schema for tax list"""

    id: str
    name: str
    rate: Decimal
    tax_type: str
    is_active: bool

    class Config:
        from_attributes = True
