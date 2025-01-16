from fastapi import APIRouter
from app.api.endpoints import auth, raffle, purchase, profile, payment

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(raffle.router, prefix="/raffles", tags=["raffles"])
api_router.include_router(purchase.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(payment.router, prefix="/payments", tags=["payments"])
