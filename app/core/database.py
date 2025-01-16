from typing import AsyncGenerator, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

# Construct database URL from Supabase settings
db_url = f"postgresql+asyncpg://postgres:{settings.SUPABASE_ANON_KEY}@db.{settings.SUPABASE_URL.split('//')[1]}/postgres"

# Configure SSL context
connect_args = {
    "ssl": True,
    "ssl_mode": "require"
}

engine = create_async_engine(
    db_url,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_supabase_client() -> Dict[str, Any]:
    """
    Get data directly from Supabase using the REST client.
    Use this for operations that don't require SQLAlchemy.
    """
    from app.core.supabase import supabase
    return supabase
