from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
from decimal import Decimal
from datetime import date
from app.models.expense import Expense
from app.models.customer import Customer
from app.models.organization import Organization
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.core.exceptions import NotFoundException, ValidationException


class ExpenseService:
    """Service for expense business logic"""

    @staticmethod
    async def get_expenses(
        db: AsyncSession,
        organization: Organization,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_billable: Optional[bool] = None,
        customer_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Expense]:
        """Get all expenses for organization with filters"""

        query = select(Expense).where(
            and_(
                Expense.organization_id == organization.id, Expense.is_deleted == False
            )
        )

        # Apply filters
        if category:
            query = query.where(Expense.category == category)

        if is_billable is not None:
            query = query.where(Expense.is_billable == is_billable)

        if customer_id:
            query = query.where(Expense.customer_id == customer_id)

        if start_date:
            query = query.where(Expense.expense_date >= start_date)

        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        query = query.offset(skip).limit(limit).order_by(Expense.expense_date.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_expense_count(
        db: AsyncSession,
        organization: Organization,
        category: Optional[str] = None,
        is_billable: Optional[bool] = None,
        customer_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Get total count of expenses"""

        query = select(func.count(Expense.id)).where(
            and_(
                Expense.organization_id == organization.id, Expense.is_deleted == False
            )
        )

        if category:
            query = query.where(Expense.category == category)

        if is_billable is not None:
            query = query.where(Expense.is_billable == is_billable)

        if customer_id:
            query = query.where(Expense.customer_id == customer_id)

        if start_date:
            query = query.where(Expense.expense_date >= start_date)

        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_expense_by_id(
        db: AsyncSession, expense_id: str, organization: Organization
    ) -> Expense:
        """Get expense by ID"""

        result = await db.execute(
            select(Expense).where(
                and_(
                    Expense.id == expense_id,
                    Expense.organization_id == organization.id,
                    Expense.is_deleted == False,
                )
            )
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise NotFoundException("Expense not found")

        return expense

    @staticmethod
    async def _generate_expense_number(
        db: AsyncSession, organization: Organization
    ) -> str:
        """Generate next expense number for organization"""

        result = await db.execute(
            select(Expense.expense_number)
            .where(Expense.organization_id == organization.id)
            .order_by(Expense.created_at.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()

        if last_number:
            try:
                num = int(last_number.split("-")[1]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"EXP-{num:05d}"

    @staticmethod
    async def create_expense(
        db: AsyncSession,
        organization: Organization,
        expense_data: ExpenseCreate,
        current_user: User,
    ) -> Expense:
        """Create a new expense"""

        # Validate customer if billable
        if expense_data.is_billable and expense_data.customer_id:
            result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.id == expense_data.customer_id,
                        Customer.organization_id == organization.id,
                        Customer.is_deleted == False,
                    )
                )
            )
            customer = result.scalar_one_or_none()

            if not customer:
                raise NotFoundException("Customer not found")
        elif expense_data.is_billable and not expense_data.customer_id:
            raise ValidationException("Customer required for billable expenses")

        # Calculate total
        total = expense_data.amount + expense_data.tax_amount

        # Generate expense number
        expense_number = await ExpenseService._generate_expense_number(db, organization)

        # Create expense
        expense = Expense(
            organization_id=organization.id,
            expense_number=expense_number,
            vendor_name=expense_data.vendor_name,
            expense_date=expense_data.expense_date,
            category=expense_data.category,
            amount=expense_data.amount,
            tax_amount=expense_data.tax_amount,
            total=total,
            payment_method=expense_data.payment_method,
            reference_number=expense_data.reference_number,
            description=expense_data.description,
            receipt_url=expense_data.receipt_url,
            is_billable=expense_data.is_billable,
            customer_id=expense_data.customer_id,
            created_by=current_user.id,
        )

        db.add(expense)
        await db.commit()
        await db.refresh(expense)

        return expense

    @staticmethod
    async def update_expense(
        db: AsyncSession,
        expense: Expense,
        expense_data: ExpenseUpdate,
        organization: Organization,
    ) -> Expense:
        """Update existing expense"""

        # Validate customer if updating billable status
        if expense_data.is_billable and expense_data.customer_id:
            result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.id == expense_data.customer_id,
                        Customer.organization_id == organization.id,
                        Customer.is_deleted == False,
                    )
                )
            )
            customer = result.scalar_one_or_none()

            if not customer:
                raise NotFoundException("Customer not found")

        # Update fields
        update_data = expense_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(expense, field, value)

        # Recalculate total if amount or tax changed
        if "amount" in update_data or "tax_amount" in update_data:
            expense.total = expense.amount + expense.tax_amount

        await db.commit()
        await db.refresh(expense)

        return expense

    @staticmethod
    async def delete_expense(db: AsyncSession, expense: Expense):
        """Soft delete expense"""

        expense.is_deleted = True

        await db.commit()

    @staticmethod
    async def get_expense_summary(
        db: AsyncSession,
        organization: Organization,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get expense summary statistics"""

        query = select(
            func.count(Expense.id).label("count"),
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

        return {
            "total_expenses": summary.count or 0,
            "total_amount": float(summary.total_amount or 0),
            "total_tax": float(summary.total_tax or 0),
        }

    @staticmethod
    async def get_expenses_by_category(
        db: AsyncSession,
        organization: Organization,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Get expenses grouped by category"""

        query = select(
            Expense.category,
            func.count(Expense.id).label("count"),
            func.sum(Expense.total).label("total"),
        ).where(
            and_(
                Expense.organization_id == organization.id, Expense.is_deleted == False
            )
        )

        if start_date:
            query = query.where(Expense.expense_date >= start_date)

        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        query = query.group_by(Expense.category).order_by(
            func.sum(Expense.total).desc()
        )

        result = await db.execute(query)

        return [
            {
                "category": row.category or "Uncategorized",
                "count": row.count,
                "total": float(row.total),
            }
            for row in result.all()
        ]
