from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "LuxeWin"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[AnyHttpUrl] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URI: str | None = None

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Supabase Configuration
    SUPABASE_URL: str = "https://utxjxjjajsxygqqpnimg.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0eGp4amphanN4eWdxcXBuaW1nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwMzM1NTMsImV4cCI6MjA1MjYwOTU1M30.vrGWwQT0exmDDwzVSqndoMRdu9Z7gl3dPHDgXXkZ22A"
    
    # Stripe Configuration
    STRIPE_API_KEY: str = "your-stripe-api-key"  # Replace with actual key from env
    STRIPE_WEBHOOK_SECRET: str = "your-stripe-webhook-secret"  # Replace with actual secret from env
    STRIPE_CURRENCY: str = "usd"
    
    # Novu Configuration
    NOVU_API_KEY: str = "your-novu-api-key"  # Replace with actual key from env
    NOVU_API_URL: str = "https://api.novu.co"
    NOVU_APP_IDENTIFIER: str = "your-novu-app-id"  # Replace with actual app ID from env
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
