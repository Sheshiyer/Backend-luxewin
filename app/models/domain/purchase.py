from datetime import datetime
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.models.domain.base import Base

class Purchase(Base):
    __tablename__ = "purchase"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    raffle_id: Mapped[int] = mapped_column(ForeignKey("raffle.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    purchase_date: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="purchases")
    raffle: Mapped["Raffle"] = relationship("Raffle", back_populates="purchases")
