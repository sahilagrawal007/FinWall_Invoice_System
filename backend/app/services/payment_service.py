from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.organization import Organization
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentGatewayCreate, PaymentVoidRequest
from app.core.exceptions import NotFoundException, ValidationException


class PaymentService:
    """Service for payment business logic"""

    @staticmethod
    async def get_payments(
        db: AsyncSession,
        organization: Organization,
        skip: int = 0,
        limit: int = 100,
        invoice_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        is_voided: Optional[bool] = None,
    ) -> List[Payment]:
        """Get all payments for organization"""

        query = select(Payment).where(Payment.organization_id == organization.id)

        if invoice_id:
            query = query.where(Payment.invoice_id == invoice_id)

        if customer_id:
            query = query.where(Payment.customer_id == customer_id)

        if is_voided is not None:
            query = query.where(Payment.is_voided == is_voided)

        query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_payment_count(
        db: AsyncSession,
        organization: Organization,
        invoice_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        is_voided: Optional[bool] = None,
    ) -> int:
        """Get total count of payments"""

        query = select(func.count(Payment.id)).where(
            Payment.organization_id == organization.id
        )

        if invoice_id:
            query = query.where(Payment.invoice_id == invoice_id)

        if customer_id:
            query = query.where(Payment.customer_id == customer_id)

        if is_voided is not None:
            query = query.where(Payment.is_voided == is_voided)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_payment_by_id(
        db: AsyncSession, payment_id: str, organization: Organization
    ) -> Payment:
        """Get payment by ID"""

        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.id == payment_id, Payment.organization_id == organization.id
                )
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise NotFoundException("Payment not found")

        return payment

    @staticmethod
    async def _generate_payment_number(
        db: AsyncSession, organization: Organization
    ) -> str:
        """Generate next payment number for organization"""

        result = await db.execute(
            select(Payment.payment_number)
            .where(Payment.organization_id == organization.id)
            .order_by(Payment.created_at.desc())
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

        return f"PAY-{num:05d}"

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        organization: Organization,
        payment_data: PaymentCreate,
        current_user: User,
    ) -> Payment:
        """
        Record a manual payment.
        This is the main method for manual payment entry.
        """

        # 1. Validate invoice
        result = await db.execute(
            select(Invoice).where(
                and_(
                    Invoice.id == payment_data.invoice_id,
                    Invoice.organization_id == organization.id,
                    Invoice.is_deleted == False,
                )
            )
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise NotFoundException("Invoice not found")

        # 2. Validate invoice status
        if invoice.status == "VOID":
            raise ValidationException("Cannot record payment for void invoice")

        if invoice.status == "DRAFT":
            raise ValidationException(
                "Cannot record payment for draft invoice. Please send the invoice first."
            )

        # 3. Validate amount
        if payment_data.amount > invoice.balance_due:
            raise ValidationException(
                f"Payment amount (₹{payment_data.amount}) exceeds balance due (₹{invoice.balance_due})"
            )

        if payment_data.amount <= 0:
            raise ValidationException("Payment amount must be greater than zero")

        # 4. Generate payment number
        payment_number = await PaymentService._generate_payment_number(db, organization)

        # 5. Create payment and update invoice in transaction
        async with db.begin_nested():
            # Create payment
            payment = Payment(
                organization_id=organization.id,
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                payment_number=payment_number,
                payment_date=payment_data.payment_date,
                amount=payment_data.amount,
                payment_method=payment_data.payment_method,
                reference_number=payment_data.reference_number,
                notes=payment_data.notes,
                created_by=current_user.id,
                # Gateway fields remain NULL for manual payments
                gateway_name=None,
                gateway_payment_id=None,
                gateway_order_id=None,
                gateway_response=None,
            )
            db.add(payment)

            # Update invoice
            invoice.amount_paid += payment_data.amount
            invoice.balance_due = invoice.total - invoice.amount_paid

            # Update invoice status
            if invoice.balance_due == 0:
                invoice.status = "PAID"
                invoice.paid_at = datetime.utcnow()
            elif invoice.amount_paid > 0:
                invoice.status = "PARTIALLY_PAID"

        await db.commit()
        await db.refresh(payment)
        await db.refresh(invoice)

        return payment

    @staticmethod
    async def record_gateway_payment(
        db: AsyncSession, organization: Organization, gateway_data: PaymentGatewayCreate
    ) -> Payment:
        """
        Record a payment from payment gateway (Razorpay/Stripe).
        This will be called by webhook handlers in Checkpoint 12+.

        NOTE: This method is ready but not used yet.
        When you add Razorpay, the webhook will call this method.
        """

        # Validate invoice (same as manual)
        result = await db.execute(
            select(Invoice).where(
                and_(
                    Invoice.id == gateway_data.invoice_id,
                    Invoice.organization_id == organization.id,
                    Invoice.is_deleted == False,
                )
            )
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status == "VOID":
            raise ValidationException("Cannot record payment for void invoice")

        # Check for duplicate gateway payment
        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.gateway_payment_id == gateway_data.gateway_payment_id,
                    Payment.organization_id == organization.id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Payment already recorded (webhook called twice)
            return existing

        # Generate payment number
        payment_number = await PaymentService._generate_payment_number(db, organization)

        # Create payment and update invoice
        async with db.begin_nested():
            payment = Payment(
                organization_id=organization.id,
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                payment_number=payment_number,
                payment_date=datetime.utcnow().date(),
                amount=gateway_data.amount,
                payment_method="ONLINE",
                reference_number=gateway_data.gateway_payment_id,
                notes=f"Payment via {gateway_data.gateway_name}",
                # Gateway fields populated
                gateway_name=gateway_data.gateway_name,
                gateway_payment_id=gateway_data.gateway_payment_id,
                gateway_order_id=gateway_data.gateway_order_id,
                gateway_response=gateway_data.gateway_response,
                created_by=None,  # Automatic payment, no user
            )
            db.add(payment)

            # Update invoice (same logic as manual)
            invoice.amount_paid += gateway_data.amount
            invoice.balance_due = invoice.total - invoice.amount_paid

            if invoice.balance_due == 0:
                invoice.status = "PAID"
                invoice.paid_at = datetime.utcnow()
            elif invoice.amount_paid > 0:
                invoice.status = "PARTIALLY_PAID"

        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def void_payment(
        db: AsyncSession,
        payment: Payment,
        void_request: PaymentVoidRequest,
        current_user: User,
    ) -> Payment:
        """Void a payment and reverse invoice balance"""

        if payment.is_voided:
            raise ValidationException("Payment is already voided")

        # Get linked invoice
        result = await db.execute(
            select(Invoice).where(Invoice.id == payment.invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise NotFoundException("Linked invoice not found")

        # Update payment and invoice in transaction
        async with db.begin_nested():
            # Void payment
            payment.is_voided = True
            payment.voided_at = datetime.utcnow()
            payment.void_reason = void_request.reason
            payment.voided_by = current_user.id

            # Reverse invoice balance
            invoice.amount_paid -= payment.amount
            invoice.balance_due = invoice.total - invoice.amount_paid

            # Recalculate invoice status
            if invoice.balance_due == invoice.total:
                # All payments voided, back to original status
                if invoice.sent_at:
                    invoice.status = "SENT"
                else:
                    invoice.status = "DRAFT"
                invoice.paid_at = None
            elif invoice.balance_due > 0:
                invoice.status = "PARTIALLY_PAID"
                invoice.paid_at = None

        await db.commit()
        await db.refresh(payment)
        await db.refresh(invoice)

        return payment
