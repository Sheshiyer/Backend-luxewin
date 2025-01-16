from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PurchaseBase(BaseModel):
    raffle_id: int
    quantity: int
    total_amount: Decimal
    transaction_id: Optional[str] = None

class PurchaseCreate(PurchaseBase):
    pass

class PurchaseUpdate(BaseModel):
    quantity: Optional[int] = None
    total_amount: Optional[Decimal] = None
    transaction_id: Optional[str] = None

class PurchaseInDBBase(PurchaseBase):
    id: int
    user_id: int
    purchase_date: datetime
    model_config = ConfigDict(from_attributes=True)

class Purchase(PurchaseInDBBase):
    pass

class PurchaseInDB(PurchaseInDBBase):
    pass
