from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseListResponse,
)
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/", response_model=dict)
async def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None),
    is_billable: Optional[bool] = Query(None),
    customer_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all expenses for the organization.

    - **skip**: Pagination offset
    - **limit**: Number of records
    - **category**: Filter by category
    - **is_billable**: Filter billable/non-billable
    - **customer_id**: Filter by customer
    - **start_date**: Filter from date
    - **end_date**: Filter to date
    """

    expenses = await ExpenseService.get_expenses(
        db=db,
        organization=organization,
        skip=skip,
        limit=limit,
        category=category,
        is_billable=is_billable,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
    )

    total = await ExpenseService.get_expense_count(
        db=db,
        organization=organization,
        category=category,
        is_billable=is_billable,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [ExpenseListResponse.model_validate(e) for e in expenses],
    }


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new expense.

    - Total = amount + tax_amount (calculated automatically)
    - If billable, customer_id required
    - Receipt URL optional (upload handled separately)
    """

    expense = await ExpenseService.create_expense(
        db=db,
        organization=organization,
        expense_data=expense_data,
        current_user=current_user,
    )

    return ExpenseResponse.model_validate(expense)


@router.get("/summary", response_model=dict)
async def get_expense_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get expense summary statistics.

    Returns total expenses count and amount.
    """

    summary = await ExpenseService.get_expense_summary(
        db=db, organization=organization, start_date=start_date, end_date=end_date
    )

    return summary


@router.get("/by-category", response_model=list)
async def get_expenses_by_category(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get expenses grouped by category.

    Useful for expense reports and charts.
    """

    categories = await ExpenseService.get_expenses_by_category(
        db=db, organization=organization, start_date=start_date, end_date=end_date
    )

    return categories


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Get expense details by ID."""

    expense = await ExpenseService.get_expense_by_id(
        db=db, expense_id=expense_id, organization=organization
    )

    return ExpenseResponse.model_validate(expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    expense_data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Update expense (partial update)."""

    expense = await ExpenseService.get_expense_by_id(
        db=db, expense_id=expense_id, organization=organization
    )

    updated_expense = await ExpenseService.update_expense(
        db=db, expense=expense, expense_data=expense_data, organization=organization
    )

    return ExpenseResponse.model_validate(updated_expense)


@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
async def delete_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Soft delete expense."""

    expense = await ExpenseService.get_expense_by_id(
        db=db, expense_id=expense_id, organization=organization
    )

    await ExpenseService.delete_expense(db=db, expense=expense)

    return {"message": "Expense deleted successfully"}
