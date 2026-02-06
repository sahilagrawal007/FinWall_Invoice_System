from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload
from typing import List, Optional
from app.models.item import Item
from app.models.tax import Tax
from app.models.organization import Organization
from app.schemas.item import ItemCreate, ItemUpdate
from app.core.exceptions import NotFoundException, DuplicateException


class ItemService:
    """Service for item business logic"""

    @staticmethod
    async def get_items(
        db: AsyncSession,
        organization: Organization,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        item_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Item]:
        """Get all items for organization with filters"""

        query = (
            select(Item)
            .options(joinedload(Item.tax))
            .where(
                and_(Item.organization_id == organization.id, Item.is_deleted == False)
            )
        )

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Item.name.ilike(f"%{search}%"),
                    Item.description.ilike(f"%{search}%"),
                    Item.sku.ilike(f"%{search}%"),
                )
            )

        if item_type:
            query = query.where(Item.item_type == item_type.upper())

        if is_active is not None:
            query = query.where(Item.is_active == is_active)

        query = query.offset(skip).limit(limit).order_by(Item.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_item_count(
        db: AsyncSession,
        organization: Organization,
        search: Optional[str] = None,
        item_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Get total count of items"""
        from sqlalchemy import func

        query = select(func.count(Item.id)).where(
            and_(Item.organization_id == organization.id, Item.is_deleted == False)
        )

        if search:
            query = query.where(
                or_(
                    Item.name.ilike(f"%{search}%"),
                    Item.description.ilike(f"%{search}%"),
                    Item.sku.ilike(f"%{search}%"),
                )
            )

        if item_type:
            query = query.where(Item.item_type == item_type.upper())

        if is_active is not None:
            query = query.where(Item.is_active == is_active)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_item_by_id(
        db: AsyncSession, item_id: str, organization: Organization
    ) -> Item:
        """Get item by ID"""

        result = await db.execute(
            select(Item)
            .options(joinedload(Item.tax))
            .where(
                and_(
                    Item.id == item_id,
                    Item.organization_id == organization.id,
                    Item.is_deleted == False,
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            raise NotFoundException("Item not found")

        return item

    @staticmethod
    async def create_item(
        db: AsyncSession, organization: Organization, item_data: ItemCreate
    ) -> Item:
        """Create a new item"""

        # Check for duplicate SKU in organization (if SKU provided)
        if item_data.sku:
            result = await db.execute(
                select(Item).where(
                    and_(
                        Item.organization_id == organization.id,
                        Item.sku == item_data.sku,
                        Item.is_deleted == False,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise DuplicateException(
                    "Item with this SKU already exists in your organization"
                )

        # Validate tax_id belongs to organization (if provided)
        if item_data.tax_id:
            result = await db.execute(
                select(Tax).where(
                    and_(
                        Tax.id == item_data.tax_id,
                        Tax.organization_id == organization.id,
                        Tax.is_deleted == False,
                    )
                )
            )
            tax = result.scalar_one_or_none()

            if not tax:
                raise NotFoundException("Tax not found")

        # Create item
        item = Item(organization_id=organization.id, **item_data.model_dump())

        db.add(item)
        await db.commit()
        await db.refresh(item)

        # Load tax relationship
        await db.refresh(item, attribute_names=["tax"])

        return item

    @staticmethod
    async def update_item(
        db: AsyncSession, item: Item, item_data: ItemUpdate, organization: Organization
    ) -> Item:
        """Update existing item"""

        # Check for duplicate SKU if SKU is being updated
        if item_data.sku:
            result = await db.execute(
                select(Item).where(
                    and_(
                        Item.organization_id == organization.id,
                        Item.sku == item_data.sku,
                        Item.id != item.id,
                        Item.is_deleted == False,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise DuplicateException(
                    "Item with this SKU already exists in your organization"
                )

        # Validate tax_id if provided
        if item_data.tax_id:
            result = await db.execute(
                select(Tax).where(
                    and_(
                        Tax.id == item_data.tax_id,
                        Tax.organization_id == organization.id,
                        Tax.is_deleted == False,
                    )
                )
            )
            tax = result.scalar_one_or_none()

            if not tax:
                raise NotFoundException("Tax not found")

        # Update fields
        update_data = item_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(item, field, value)

        await db.commit()
        await db.refresh(item)
        await db.refresh(item, attribute_names=["tax"])

        return item

    @staticmethod
    async def delete_item(db: AsyncSession, item: Item):
        """Soft delete item"""

        item.is_deleted = True
        item.is_active = False

        await db.commit()
