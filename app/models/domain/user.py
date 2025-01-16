from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from app.models.domain.base import Base
from app.models.domain.raffle import Raffle
from app.models.domain.purchase import Purchase


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    wallet_address: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Relationships
    won_raffles: Mapped[List["Raffle"]] = relationship(
        "Raffle", back_populates="winner"
    )
    purchases: Mapped[List["Purchase"]] = relationship(
        "Purchase", back_populates="user"
    )
