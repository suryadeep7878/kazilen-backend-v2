from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.db.database import get_db
from app.schemas.payment import SubscriptionVerifyRequest
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/subscription/order")
def create_subscription_order(
    plan_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Worker creates a Razorpay order for a membership plan.

    Amount is taken from membership_plans.price (Rs -> paise server-side).
    """
    return PaymentService.create_subscription_order(current_user.id, plan_id, db)


@router.post("/subscription/verify")
def verify_subscription_payment(
    payload: SubscriptionVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Client-side verify after checkout.js success (HMAC + fetch captured)."""
    return PaymentService.verify_subscription_payment(
        current_user.id,
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
        db,
    )


@router.get("/subscription/status/{order_id}")
def subscription_order_status(
    order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Poll order status (used when checkout modal is closed mid-flow)."""
    return PaymentService.order_status(current_user.id, order_id, db)


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Razorpay server webhook — signature over RAW body.

    No JWT auth: authenticity comes from x-razorpay-signature HMAC with
    RAZORPAY_WEBHOOK_SECRET (same as live_wahhtrips verifyPayment).
    Register https://<host>/api/payments/webhook in the Razorpay dashboard
    for events payment.captured / payment.failed.
    """
    raw = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    return PaymentService.handle_webhook(raw, signature, payload or {}, db)


@router.get("/admin/payments")
def admin_payments(
    worker_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Admin read-only view of online subscription payments (manual subs not listed)."""
    return PaymentService.list_payments(db, worker_id=worker_id, status_filter=status, limit=limit, offset=offset)
