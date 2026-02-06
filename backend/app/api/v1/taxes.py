from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.tax import TaxCreate, TaxUpdate, TaxResponse, TaxListResponse
from app.services.tax_service import TaxService

router = APIRouter(prefix="/taxes", tags=["Taxes"])


@router.get("/", response_model=list[TaxListResponse])
async def list_taxes(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all taxes for the organization.

    - **is_active**: Filter by active status
    """

    taxes = await TaxService.get_taxes(
        db=db, organization=organization, is_active=is_active
    )

    return [TaxListResponse.model_validate(t) for t in taxes]


@router.post("/", response_model=TaxResponse, status_code=status.HTTP_201_CREATED)
async def create_tax(
    tax_data: TaxCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tax rate.

    - Name must be unique within organization
    - Rate is percentage (e.g., 18.00 for 18%)
    """

    tax = await TaxService.create_tax(
        db=db, organization=organization, tax_data=tax_data
    )

    return TaxResponse.model_validate(tax)


@router.get("/{tax_id}", response_model=TaxResponse)
async def get_tax(
    tax_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Get tax details by ID."""

    tax = await TaxService.get_tax_by_id(
        db=db, tax_id=tax_id, organization=organization
    )

    return TaxResponse.model_validate(tax)


@router.patch("/{tax_id}", response_model=TaxResponse)
async def update_tax(
    tax_id: str,
    tax_data: TaxUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Update tax (partial update)."""

    tax = await TaxService.get_tax_by_id(
        db=db, tax_id=tax_id, organization=organization
    )

    updated_tax = await TaxService.update_tax(
        db=db, tax=tax, tax_data=tax_data, organization=organization
    )

    return TaxResponse.model_validate(updated_tax)


@router.delete("/{tax_id}", status_code=status.HTTP_200_OK)
async def delete_tax(
    tax_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Soft delete tax."""

    tax = await TaxService.get_tax_by_id(
        db=db, tax_id=tax_id, organization=organization
    )

    await TaxService.delete_tax(db=db, tax=tax)

    return {"message": "Tax deleted successfully"}