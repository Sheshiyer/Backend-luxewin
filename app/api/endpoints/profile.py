from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.models.schemas.user import UserUpdate
from app.models.domain.purchase import Purchase
from app.models.domain.raffle import Raffle
from app.core.supabase import supabase

router = APIRouter()

@router.get("/me")
async def get_profile(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current user's profile.
    """
    return current_user

@router.put("/me")
async def update_profile(
    *,
    current_user: dict = Depends(get_current_active_user),
    user_update: UserUpdate
) -> Dict[str, Any]:
    """
    Update current user's profile.
    """
    try:
        # Update user data in Supabase
        update_data = user_update.model_dump(exclude_unset=True)
        response = (
            supabase.table('users')
            .update(update_data)
            .eq('id', current_user['id'])
            .execute()
        )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me/stats")
async def get_profile_stats(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current user's raffle participation statistics.
    Returns:
    - Total tickets purchased
    - Total amount spent
    - Number of raffles participated in
    - Number of raffles won
    """
    # Get purchase stats
    purchase_stats = await db.execute(
        select(
            func.count(Purchase.id).label('total_purchases'),
            func.sum(Purchase.quantity).label('total_tickets'),
            func.sum(Purchase.total_amount).label('total_spent')
        ).where(Purchase.user_id == current_user['id'])
    )
    stats = purchase_stats.first()

    # Get number of unique raffles participated in
    unique_raffles = await db.execute(
        select(func.count(func.distinct(Purchase.raffle_id)))
        .where(Purchase.user_id == current_user['id'])
    )
    raffles_count = unique_raffles.scalar()

    # Get number of raffles won
    won_raffles = await db.execute(
        select(func.count(Raffle.id))
        .where(Raffle.winner_id == current_user['id'])
    )
    won_count = won_raffles.scalar()

    return {
        "total_purchases": stats[0] or 0,
        "total_tickets": stats[1] or 0,
        "total_spent": float(stats[2] or 0),
        "raffles_participated": raffles_count or 0,
        "raffles_won": won_count or 0
    }

@router.get("/me/raffles")
async def get_user_raffles(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get list of raffles the user has participated in,
    including number of tickets purchased for each raffle.
    """
    # Get user's raffle participations with ticket counts
    query = (
        select(
            Raffle,
            func.sum(Purchase.quantity).label('tickets_bought'),
            func.sum(Purchase.total_amount).label('amount_spent')
        )
        .join(Purchase, Purchase.raffle_id == Raffle.id)
        .where(Purchase.user_id == current_user['id'])
        .group_by(Raffle.id)
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    raffles_data = []
    
    for raffle, tickets, amount in result:
        raffle_dict = {
            "id": raffle.id,
            "title": raffle.title,
            "description": raffle.description,
            "ticket_price": float(raffle.ticket_price),
            "total_tickets": raffle.total_tickets,
            "tickets_sold": raffle.tickets_sold,
            "start_date": raffle.start_date,
            "end_date": raffle.end_date,
            "is_active": raffle.is_active,
            "tickets_bought": tickets,
            "amount_spent": float(amount),
            "won": raffle.winner_id == current_user['id']
        }
        raffles_data.append(raffle_dict)
    
    return {
        "total": len(raffles_data),
        "raffles": raffles_data
    }
