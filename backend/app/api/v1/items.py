from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("/", response_model=dict)
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None, pattern="^(PRODUCT|SERVICE)$"),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all items for the organization.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **search**: Search by name, description, or SKU
    - **item_type**: Filter by PRODUCT or SERVICE
    - **is_active**: Filter by active status
    """

    items = await ItemService.get_items(
        db=db,
        organization=organization,
        skip=skip,
        limit=limit,
        search=search,
        item_type=item_type,
        is_active=is_active,
    )

    total = await ItemService.get_item_count(
        db=db,
        organization=organization,
        search=search,
        item_type=item_type,
        is_active=is_active,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [ItemListResponse.model_validate(i) for i in items],
    }


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new item (product or service).

    - SKU must be unique within organization (if provided)
    - tax_id is optional (default tax for this item)
    """

    item = await ItemService.create_item(
        db=db, organization=organization, item_data=item_data
    )

    return ItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Get item details by ID."""

    item = await ItemService.get_item_by_id(
        db=db, item_id=item_id, organization=organization
    )

    return ItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item_data: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Update item (partial update)."""

    item = await ItemService.get_item_by_id(
        db=db, item_id=item_id, organization=organization
    )

    updated_item = await ItemService.update_item(
        db=db, item=item, item_data=item_data, organization=organization
    )

    return ItemResponse.model_validate(updated_item)


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Soft delete item."""

    item = await ItemService.get_item_by_id(
        db=db, item_id=item_id, organization=organization
    )

    await ItemService.delete_item(db=db, item=item)

    return {"message": "Item deleted successfully"}
