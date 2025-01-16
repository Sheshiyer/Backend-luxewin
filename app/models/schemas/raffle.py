from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RaffleBase(BaseModel):
    title: str
    description: Optional[str] = None
    ticket_price: Decimal
    total_tickets: int
    end_date: datetime

class RaffleCreate(RaffleBase):
    pass

class RaffleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ticket_price: Optional[Decimal] = None
    total_tickets: Optional[int] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class RaffleInDBBase(RaffleBase):
    id: int
    tickets_sold: int
    start_date: datetime
    is_active: bool
    winner_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class Raffle(RaffleInDBBase):
    pass

class RaffleInDB(RaffleInDBBase):
    pass
