from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.models.schemas.purchase import (
    Purchase,
    PurchaseCreate
)
from app.models.domain.purchase import Purchase as PurchaseModel
from app.models.domain.raffle import Raffle as RaffleModel
from app.services.notifications import notification_service
from app.services.notification_templates import NotificationTemplate
from app.services.payments import payment_service

router = APIRouter()

@router.post("/", response_model=Purchase)
async def create_purchase(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    purchase_in: PurchaseCreate
) -> PurchaseModel:
    """
    Create a new purchase (buy raffle tickets).
    Validates:
    - Raffle exists and is active
    - Enough tickets are available
    - Total amount matches ticket price * quantity
    - Payment is confirmed
    """
    # Get raffle to validate
    raffle = await db.get(RaffleModel, purchase_in.raffle_id)
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
    
    # Validate total amount
    expected_amount = float(raffle.ticket_price) * purchase_in.quantity
    if float(purchase_in.total_amount) != expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid total amount"
        )
    
    # Verify payment
    payment_confirmed = await payment_service.confirm_payment(
        purchase_in.payment_intent_id
    )
    if not payment_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment not confirmed"
        )
    
    # Create purchase
    purchase = PurchaseModel(
        user_id=current_user['id'],
        raffle_id=purchase_in.raffle_id,
        quantity=purchase_in.quantity,
        total_amount=purchase_in.total_amount,
        payment_intent_id=purchase_in.payment_intent_id
    )
    
    try:
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        
        # Send purchase confirmation notification
        await notification_service.trigger_event(
            name=NotificationTemplate.TICKET_PURCHASE,
            subscriber_id=current_user['id'],
            payload={
                "full_name": current_user.get('full_name', ''),
                "raffle_title": raffle.title,
                "quantity": purchase_in.quantity,
                "total_amount": float(purchase_in.total_amount)
            }
        )
        
        return purchase
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[Purchase])
async def list_user_purchases(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> List[PurchaseModel]:
    """
    List all purchases for the current user.
    """
    query = (
        select(PurchaseModel)
        .where(PurchaseModel.user_id == current_user['id'])
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{purchase_id}", response_model=Purchase)
async def get_purchase(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    purchase_id: int
) -> PurchaseModel:
    """
    Get a specific purchase by ID.
    Only returns the purchase if it belongs to the current user.
    """
    purchase = await db.get(PurchaseModel, purchase_id)
    if not purchase or purchase.user_id != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    return purchase

@router.get("/raffle/{raffle_id}", response_model=List[Purchase])
async def list_raffle_purchases(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    raffle_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[PurchaseModel]:
    """
    List all purchases for a specific raffle.
    Only returns the current user's purchases for that raffle.
    """
    query = (
        select(PurchaseModel)
        .where(
            PurchaseModel.raffle_id == raffle_id,
            PurchaseModel.user_id == current_user['id']
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
