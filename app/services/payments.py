from typing import Dict, Any, Optional
import stripe
from fastapi import HTTPException, status

from app.core.config import settings

# Initialize Stripe with API key
stripe.api_key = settings.STRIPE_API_KEY

class PaymentService:
    @staticmethod
    async def create_payment_intent(
        amount: float,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent for a purchase.
        
        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Currency code (default: usd)
            metadata: Additional metadata for the payment
        
        Returns:
            Payment intent details including client secret
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={
                    "enabled": True
                }
            )
            
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def confirm_payment(payment_intent_id: str) -> bool:
        """
        Confirm that a payment was successful.
        
        Args:
            payment_intent_id: The ID of the payment intent to check
            
        Returns:
            True if payment was successful, False otherwise
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent.status == "succeeded"
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def refund_payment(
        payment_intent_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.
        
        Args:
            payment_intent_id: The ID of the payment to refund
            amount: Optional amount to refund (in dollars). If not provided, full amount is refunded.
            
        Returns:
            Refund details
        """
        try:
            refund_params = {"payment_intent": payment_intent_id}
            
            if amount:
                refund_params["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100  # Convert cents to dollars
            }
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def handle_webhook_event(
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Raw request body
            sig_header: Stripe signature header
            
        Returns:
            Processed event data
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Handle specific event types
            if event.type == "payment_intent.succeeded":
                payment_intent = event.data.object
                # Handle successful payment
                return {
                    "status": "success",
                    "payment_intent_id": payment_intent.id,
                    "amount": payment_intent.amount / 100,
                    "metadata": payment_intent.metadata
                }
            
            elif event.type == "payment_intent.payment_failed":
                payment_intent = event.data.object
                # Handle failed payment
                return {
                    "status": "failed",
                    "payment_intent_id": payment_intent.id,
                    "error": payment_intent.last_payment_error
                }
            
            # Return raw event data for other event types
            return {"status": "unhandled", "type": event.type}
            
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

# Create a global instance
payment_service = PaymentService()
