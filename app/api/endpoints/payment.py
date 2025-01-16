from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.core.config import settings
from app.services.payments import payment_service
from app.models.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentConfirmation,
    PaymentRefund,
    PaymentRefundResponse,
    WebhookEvent
)
from app.models.domain.raffle import Raffle as RaffleModel

router = APIRouter()

@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    payment_data: PaymentIntentCreate
) -> Dict[str, Any]:
    """
    Create a payment intent for purchasing raffle tickets.
    """
    # Get raffle to calculate amount
    raffle = await db.get(RaffleModel, payment_data.raffle_id)
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    if not raffle.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raffle is not active"
        )
    
    # Calculate total amount
    total_amount = float(raffle.ticket_price) * payment_data.quantity
    
    # Create payment intent
    payment_intent = await payment_service.create_payment_intent(
        amount=total_amount,
        currency=settings.STRIPE_CURRENCY,
        metadata={
            "user_id": current_user['id'],
            "raffle_id": payment_data.raffle_id,
            "quantity": payment_data.quantity
        }
    )
    
    return {
        "client_secret": payment_intent["client_secret"],
        "payment_intent_id": payment_intent["payment_intent_id"],
        "amount": total_amount,
        "currency": settings.STRIPE_CURRENCY
    }

@router.post("/confirm", response_model=Dict[str, bool])
async def confirm_payment(
    *,
    current_user: dict = Depends(get_current_active_user),
    confirmation: PaymentConfirmation
) -> Dict[str, bool]:
    """
    Confirm a payment was successful.
    """
    is_confirmed = await payment_service.confirm_payment(
        confirmation.payment_intent_id
    )
    return {"confirmed": is_confirmed}

@router.post("/refund", response_model=PaymentRefundResponse)
async def refund_payment(
    *,
    current_user: dict = Depends(get_current_active_user),
    refund_data: PaymentRefund
) -> Dict[str, Any]:
    """
    Refund a payment.
    Only available to superusers.
    """
    if not current_user.get('is_superuser'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await payment_service.refund_payment(
        payment_intent_id=refund_data.payment_intent_id,
        amount=refund_data.amount
    )

@router.post("/webhook", response_model=WebhookEvent)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
) -> Dict[str, Any]:
    """
    Handle Stripe webhook events.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No signature provided"
        )
    
    # Get the raw request body
    payload = await request.body()
    
    # Process the webhook event
    event_data = await payment_service.handle_webhook_event(
        payload=payload,
        sig_header=stripe_signature
    )
    
    return {
        "type": event_data.get("type", "unknown"),
        "data": event_data
    }
