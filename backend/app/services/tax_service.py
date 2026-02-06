from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.models.tax import Tax
from app.models.organization import Organization
from app.schemas.tax import TaxCreate, TaxUpdate
from app.core.exceptions import NotFoundException, DuplicateException


class TaxService:
    """Service for tax business logic"""

    @staticmethod
    async def get_taxes(
        db: AsyncSession, organization: Organization, is_active: Optional[bool] = None
    ) -> List[Tax]:
        """Get all taxes for organization"""

        query = select(Tax).where(
            and_(Tax.organization_id == organization.id, Tax.is_deleted == False)
        )

        if is_active is not None:
            query = query.where(Tax.is_active == is_active)

        query = query.order_by(Tax.rate.asc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_tax_by_id(
        db: AsyncSession, tax_id: str, organization: Organization
    ) -> Tax:
        """Get tax by ID"""

        result = await db.execute(
            select(Tax).where(
                and_(
                    Tax.id == tax_id,
                    Tax.organization_id == organization.id,
                    Tax.is_deleted == False,
                )
            )
        )
        tax = result.scalar_one_or_none()

        if not tax:
            raise NotFoundException("Tax not found")

        return tax

    @staticmethod
    async def create_tax(
        db: AsyncSession, organization: Organization, tax_data: TaxCreate
    ) -> Tax:
        """Create a new tax"""

        # Check for duplicate name in organization
        result = await db.execute(
            select(Tax).where(
                and_(
                    Tax.organization_id == organization.id,
                    Tax.name == tax_data.name,
                    Tax.is_deleted == False,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise DuplicateException(
                "Tax with this name already exists in your organization"
            )

        # Create tax
        tax = Tax(organization_id=organization.id, **tax_data.model_dump())

        db.add(tax)
        await db.commit()
        await db.refresh(tax)

        return tax

    @staticmethod
    async def update_tax(
        db: AsyncSession, tax: Tax, tax_data: TaxUpdate, organization: Organization
    ) -> Tax:
        """Update existing tax"""

        # Check for duplicate name if name is being updated
        if tax_data.name:
            result = await db.execute(
                select(Tax).where(
                    and_(
                        Tax.organization_id == organization.id,
                        Tax.name == tax_data.name,
                        Tax.id != tax.id,
                        Tax.is_deleted == False,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise DuplicateException(
                    "Tax with this name already exists in your organization"
                )

        # Update fields
        update_data = tax_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(tax, field, value)

        await db.commit()
        await db.refresh(tax)

        return tax

    @staticmethod
    async def delete_tax(db: AsyncSession, tax: Tax):
        """Soft delete tax"""

        tax.is_deleted = True
        tax.is_active = False

        await db.commit()
