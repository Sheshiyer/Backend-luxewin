from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.domain.base import Base

class Raffle(Base):
    title = Column(String, nullable=False)
    description = Column(String)
    ticket_price = Column(Numeric(10, 2), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    tickets_sold = Column(Integer, default=0)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    winner_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Relationships
    winner = relationship("User", back_populates="won_raffles")
    purchases = relationship("Purchase", back_populates="raffle")
