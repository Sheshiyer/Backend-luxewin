import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def create_database() -> None:
    # Connect to default database to create new database
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/postgres",
        isolation_level="AUTOCOMMIT",
    )

    from sqlalchemy import text
    async with engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}'")
        )
        exists = result.scalar() is not None

        if not exists:
            await conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
            print(f"Created database {settings.POSTGRES_DB}")
        else:
            print(f"Database {settings.POSTGRES_DB} already exists")

def run_migrations() -> None:
    # Create initial migration
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
    
    # Run the migration
    command.upgrade(alembic_cfg, "head")
    print("Applied database migrations")

async def main() -> None:
    print("Creating database...")
    await create_database()
    
    print("Running migrations...")
    run_migrations()
    
    print("Database initialization completed")

if __name__ == "__main__":
    asyncio.run(main())
