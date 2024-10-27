"""
Database reset script for cleaning and reinitializing the database.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models import Base
from app.core.database import async_session
from sqlalchemy import text

async def reset_database():
    print("Connecting to database...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )

    async with engine.begin() as conn:
        print("\nDropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("\nCreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # Reset sequences
        print("\nResetting sequences...")
        sequences = [
            "authors_id_seq",
            "texts_id_seq",
            "text_divisions_id_seq",
            "text_lines_id_seq"
        ]
        for seq in sequences:
            try:
                await conn.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                print(f"Reset sequence: {seq}")
            except Exception as e:
                print(f"Error resetting sequence {seq}: {e}")

    print("\nDatabase reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_database())
