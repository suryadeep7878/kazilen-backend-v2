from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionOrderResponse(BaseModel):
    status: str = "success"
    order_id: str
    amount: int  # paise (price Rs * 100, as sent to Razorpay)
    currency: str = "INR"
    key_id: str  # public key id for checkout.js (safe to expose)
    plan_id: int
    plan_name: Optional[str] = None
    payment_id: int  # subscription_payments.id for status polling


class SubscriptionVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=1)
    razorpay_payment_id: str = Field(..., min_length=1)
    razorpay_signature: str = Field(..., min_length=1)


class SubscriptionPaymentResponse(BaseModel):
    id: int
    worker_id: int
    worker_name: Optional[str] = None
    plan_id: int
    plan_name: Optional[str] = None
    subscription_id: Optional[int] = None
    amount: int
    currency: str = "INR"
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    created_at: Optional[str] = None
