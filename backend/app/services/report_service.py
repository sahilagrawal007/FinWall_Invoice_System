from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.expense import Expense
from app.models.customer import Customer
from app.models.organization import Organization


class ReportService:
    """Service for generating reports"""

    @staticmethod
    async def get_sales_summary(
        db: AsyncSession,
        organization: Organization,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get sales summary statistics"""

        query = select(
            func.count(Invoice.id).label("total_invoices"),
            func.sum(Invoice.total).label("total_sales"),
            func.sum(Invoice.tax_total).label("total_tax"),
            func.sum(Invoice.amount_paid).label("total_paid"),
            func.sum(Invoice.balance_due).label("total_outstanding"),
        ).where(
            and_(
                Invoice.organization_id == organization.id,
                Invoice.is_deleted == False,
                Invoice.status != "VOID",
            )
        )

        if start_date:
            query = query.where(Invoice.invoice_date >= start_date)

        if end_date:
            query = query.where(Invoice.invoice_date <= end_date)

        result = await db.execute(query)
        summary = result.one()

        return {
            "total_invoices": summary.total_invoices or 0,
            "total_sales": float(summary.total_sales or 0),
            "total_tax": float(summary.total_tax or 0),
            "total_paid": float(summary.total_paid or 0),
            "total_outstanding": float(summary.total_outstanding or 0),
        }

    @staticmethod
    async def get_ar_aging_summary(
        db: AsyncSession, organization: Organization
    ) -> dict:
        """Get Accounts Receivable aging summary"""

        today = date.today()

        # Get all unpaid invoices
        query = select(Invoice).where(
            and_(
                Invoice.organization_id == organization.id,
                Invoice.is_deleted == False,
                Invoice.balance_due > 0,
                Invoice.status != "VOID",
            )
        )

        result = await db.execute(query)
        invoices = result.scalars().all()

        # Initialize aging buckets
        aging = {
            "current": {"count": 0, "amount": 0},  # 0-30 days
            "days_31_60": {"count": 0, "amount": 0},  # 31-60 days
            "days_61_90": {"count": 0, "amount": 0},  # 61-90 days
            "over_90": {"count": 0, "amount": 0},  # 90+ days
            "total": {"count": 0, "amount": 0},
        }

        for invoice in invoices:
            days_overdue = (today - invoice.due_date).days
            balance = float(invoice.balance_due)

            aging["total"]["count"] += 1
            aging["total"]["amount"] += balance

            if days_overdue <= 30:
                aging["current"]["count"] += 1
                aging["current"]["amount"] += balance
            elif days_overdue <= 60:
                aging["days_31_60"]["count"] += 1
                aging["days_31_60"]["amount"] += balance
            elif days_overdue <= 90:
                aging["days_61_90"]["count"] += 1
                aging["days_61_90"]["amount"] += balance
            else:
                aging["over_90"]["count"] += 1
                aging["over_90"]["amount"] += balance

        return aging

    @staticmethod
    async def get_customer_balance_summary(
        db: AsyncSession, organization: Organization
    ) -> list:
        """Get outstanding balance per customer"""

        query = (
            select(
                Customer.id,
                Customer.name,
                func.sum(Invoice.balance_due).label("outstanding_balance"),
                func.count(Invoice.id).label("unpaid_invoices"),
            )
            .join(Invoice, Invoice.customer_id == Customer.id)
            .where(
                and_(
                    Customer.organization_id == organization.id,
                    Customer.is_deleted == False,
                    Invoice.is_deleted == False,
                    Invoice.balance_due > 0,
                    Invoice.status != "VOID",
                )
            )
            .group_by(Customer.id, Customer.name)
            .order_by(func.sum(Invoice.balance_due).desc())
        )

        result = await db.execute(query)

        return [
            {
                "customer_id": str(row.id),
                "customer_name": row.name,
                "outstanding_balance": float(row.outstanding_balance or 0),
                "unpaid_invoices": row.unpaid_invoices,
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_payment_summary(
        db: AsyncSession,
        organization: Organization,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get payment summary statistics"""

        # Total payments
        query = select(
            func.count(Payment.id).label("total_payments"),
            func.sum(Payment.amount).label("total_amount"),
        ).where(
            and_(Payment.organization_id == organization.id, Payment.is_voided == False)
        )

        if start_date:
            query = query.where(Payment.payment_date >= start_date)

        if end_date:
            query = query.where(Payment.payment_date <= end_date)

        result = await db.execute(query)
        summary = result.one()

        # Payment methods breakdown
        method_query = select(
            Payment.payment_method,
            func.count(Payment.id).label("count"),
            func.sum(Payment.amount).label("amount"),
        ).where(
            and_(Payment.organization_id == organization.id, Payment.is_voided == False)
        )

        if start_date:
            method_query = method_query.where(Payment.payment_date >= start_date)

        if end_date:
            method_query = method_query.where(Payment.payment_date <= end_date)

        method_query = method_query.group_by(Payment.payment_method)

        method_result = await db.execute(method_query)

        methods = [
            {
                "method": row.payment_method,
                "count": row.count,
                "amount": float(row.amount or 0),
            }
            for row in method_result.all()
        ]

        return {
            "total_payments": summary.total_payments or 0,
            "total_amount": float(summary.total_amount or 0),
            "by_method": methods,
        }

    @staticmethod
    async def get_expense_summary(
        db: AsyncSession,
        organization: Organization,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get expense summary statistics"""

        query = select(
            func.count(Expense.id).label("total_expenses"),
            func.sum(Expense.total).label("total_amount"),
            func.sum(Expense.tax_amount).label("total_tax"),
        ).where(
            and_(
                Expense.organization_id == organization.id, Expense.is_deleted == False
            )
        )

        if start_date:
            query = query.where(Expense.expense_date >= start_date)

        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        result = await db.execute(query)
        summary = result.one()

        # By category
        category_query = select(
            Expense.category,
            func.count(Expense.id).label("count"),
            func.sum(Expense.total).label("amount"),
        ).where(
            and_(
                Expense.organization_id == organization.id, Expense.is_deleted == False
            )
        )

        if start_date:
            category_query = category_query.where(Expense.expense_date >= start_date)

        if end_date:
            category_query = category_query.where(Expense.expense_date <= end_date)

        category_query = category_query.group_by(Expense.category).order_by(
            func.sum(Expense.total).desc()
        )

        category_result = await db.execute(category_query)

        categories = [
            {
                "category": row.category or "Uncategorized",
                "count": row.count,
                "amount": float(row.amount or 0),
            }
            for row in category_result.all()
        ]

        return {
            "total_expenses": summary.total_expenses or 0,
            "total_amount": float(summary.total_amount or 0),
            "total_tax": float(summary.total_tax or 0),
            "by_category": categories,
        }

    @staticmethod
    async def get_sales_by_customer(
        db: AsyncSession,
        organization: Organization,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
    ) -> list:
        """Get top customers by sales"""

        query = (
            select(
                Customer.id,
                Customer.name,
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.total).label("total_sales"),
            )
            .join(Invoice, Invoice.customer_id == Customer.id)
            .where(
                and_(
                    Customer.organization_id == organization.id,
                    Customer.is_deleted == False,
                    Invoice.is_deleted == False,
                    Invoice.status != "VOID",
                )
            )
        )

        if start_date:
            query = query.where(Invoice.invoice_date >= start_date)

        if end_date:
            query = query.where(Invoice.invoice_date <= end_date)

        query = (
            query.group_by(Customer.id, Customer.name)
            .order_by(func.sum(Invoice.total).desc())
            .limit(limit)
        )

        result = await db.execute(query)

        return [
            {
                "customer_id": str(row.id),
                "customer_name": row.name,
                "invoice_count": row.invoice_count,
                "total_sales": float(row.total_sales or 0),
            }
            for row in result.all()
        ]
