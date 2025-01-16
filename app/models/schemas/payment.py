from typing import Optional
from pydantic import BaseModel, ConfigDict

class PaymentIntentCreate(BaseModel):
    raffle_id: int
    quantity: int

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str
    model_config = ConfigDict(from_attributes=True)

class PaymentConfirmation(BaseModel):
    payment_intent_id: str

class PaymentRefund(BaseModel):
    payment_intent_id: str
    amount: Optional[float] = None

class PaymentRefundResponse(BaseModel):
    refund_id: str
    status: str
    amount: float
    model_config = ConfigDict(from_attributes=True)

class WebhookEvent(BaseModel):
    type: str
    data: dict
    model_config = ConfigDict(from_attributes=True)
