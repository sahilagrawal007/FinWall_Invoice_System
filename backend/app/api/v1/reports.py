from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/sales-summary")
async def get_sales_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get sales summary report.

    Returns total sales, tax, paid, and outstanding amounts.
    """

    summary = await ReportService.get_sales_summary(
        db=db, organization=organization, start_date=start_date, end_date=end_date
    )

    return summary


@router.get("/ar-aging")
async def get_ar_aging(
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get Accounts Receivable aging report.

    Groups unpaid invoices by age: 0-30, 31-60, 61-90, 90+ days.
    """

    aging = await ReportService.get_ar_aging_summary(db=db, organization=organization)

    return aging


@router.get("/customer-balances")
async def get_customer_balances(
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get customer balance summary.

    Shows outstanding balance per customer.
    """

    balances = await ReportService.get_customer_balance_summary(
        db=db, organization=organization
    )

    return balances


@router.get("/payment-summary")
async def get_payment_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get payment summary report.

    Total payments received and breakdown by payment method.
    """

    summary = await ReportService.get_payment_summary(
        db=db, organization=organization, start_date=start_date, end_date=end_date
    )

    return summary


@router.get("/expense-summary")
async def get_expense_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get expense summary report.

    Total expenses and breakdown by category.
    """

    summary = await ReportService.get_expense_summary(
        db=db, organization=organization, start_date=start_date, end_date=end_date
    )

    return summary


@router.get("/sales-by-customer")
async def get_sales_by_customer(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get top customers by sales.

    Useful for charts and customer analysis.
    """

    customers = await ReportService.get_sales_by_customer(
        db=db,
        organization=organization,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return customers
