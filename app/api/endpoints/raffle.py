from typing import List, Optional
from datetime import datetime, timedelta
import random
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.core.database import get_db
from app.models.schemas.raffle import (
    Raffle,
    RaffleCreate,
    RaffleUpdate
)
from app.models.domain.raffle import Raffle as RaffleModel
from app.models.domain.purchase import Purchase as PurchaseModel
from app.services.notifications import notification_service
from app.services.notification_templates import NotificationTemplate

router = APIRouter()

async def check_ending_soon(
    db: AsyncSession,
    raffle: RaffleModel
) -> None:
    """Check if raffle is ending soon and notify participants"""
    if raffle.end_date - timedelta(hours=24) <= datetime.utcnow() <= raffle.end_date:
        # Get all participants
        query = (
            select(PurchaseModel.user_id)
            .where(PurchaseModel.raffle_id == raffle.id)
            .distinct()
        )
        result = await db.execute(query)
        participants = result.scalars().all()
        
        # Notify each participant
        for user_id in participants:
            await notification_service.trigger_event(
                name=NotificationTemplate.RAFFLE_ENDING,
                subscriber_id=user_id,
                payload={
                    "raffle_title": raffle.title,
                    "end_time": raffle.end_date.isoformat()
                }
            )

async def select_winner(
    db: AsyncSession,
    raffle_id: int
) -> Optional[str]:
    """Select a random winner from raffle participants"""
    # Get all tickets as individual entries
    query = (
        select(PurchaseModel.user_id)
        .where(
            PurchaseModel.raffle_id == raffle_id,
        )
    )
    result = await db.execute(query)
    tickets = result.scalars().all()
    
    if not tickets:
        return None
    
    # Select random winner
    winner_id = random.choice(tickets)
    return winner_id

@router.post("/", response_model=Raffle)
async def create_raffle(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    raffle_in: RaffleCreate,
    background_tasks: BackgroundTasks
) -> RaffleModel:
    """
    Create new raffle.
    Only superusers can create raffles.
    """
    if not current_user.get('is_superuser'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    raffle = RaffleModel(**raffle_in.model_dump())
    db.add(raffle)
    await db.commit()
    await db.refresh(raffle)
    # Check if raffle is ending soon
    background_tasks.add_task(check_ending_soon, db, raffle)
    return raffle

@router.get("/", response_model=List[Raffle])
async def list_raffles(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
) -> List[RaffleModel]:
    """
    List all raffles.
    Optionally filter by active status.
    """
    query = select(RaffleModel)
    if active_only:
        query = query.where(RaffleModel.is_active == True)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{raffle_id}", response_model=Raffle)
async def get_raffle(
    *,
    db: AsyncSession = Depends(get_db),
    raffle_id: int
) -> RaffleModel:
    """
    Get raffle by ID.
    """
    raffle = await db.get(RaffleModel, raffle_id)
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    return raffle

@router.put("/{raffle_id}", response_model=Raffle)
async def update_raffle(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    raffle_id: int,
    raffle_in: RaffleUpdate
) -> RaffleModel:
    """
    Update raffle.
    Only superusers can update raffles.
    """
    if not current_user.get('is_superuser'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    raffle = await db.get(RaffleModel, raffle_id)
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    update_data = raffle_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(raffle, field, value)
    
    await db.commit()
    await db.refresh(raffle)
    return raffle

@router.post("/{raffle_id}/select-winner", response_model=Raffle)
async def select_raffle_winner(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    raffle_id: int
) -> RaffleModel:
    """
    Select a winner for the raffle.
    Only superusers can select winners.
    """
    if not current_user.get('is_superuser'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    raffle = await db.get(RaffleModel, raffle_id)
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    if raffle.winner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Winner already selected"
        )
    
    if raffle.end_date > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raffle has not ended yet"
        )
    
    winner_id = await select_winner(db, raffle_id)
    if not winner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No participants in raffle"
        )
    
    # Update raffle with winner
    raffle.winner_id = winner_id
    raffle.is_active = False
    await db.commit()
    await db.refresh(raffle)
    
    # Notify winner
    await notification_service.trigger_event(
        name=NotificationTemplate.RAFFLE_WINNER,
        subscriber_id=winner_id,
        payload={
            "raffle_title": raffle.title
        }
    )
    
    return raffle

router.delete("/{raffle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_raffle(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    raffle_id: int
):
    """
    Delete raffle.
    Only superusers can delete raffles.
    """
    if not current_user.get('is_superuser'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    raffle = await db.get(RaffleModel, raffle_id)
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    await db.delete(raffle)
    await db.commit()
