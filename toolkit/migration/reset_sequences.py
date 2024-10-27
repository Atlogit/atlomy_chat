"""Script to reset all sequences in the database after clearing data."""
from app.core.database import async_session
import asyncio
from sqlalchemy import text

async def reset_sequences():
    """Reset all sequences in the database to start from 1."""
    async with async_session() as session:
        # Get all sequences
        result = await session.execute(
            text("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
            """)
        )
        sequences = result.scalars().all()
        
        # Reset each sequence
        for seq in sequences:
            await session.execute(
                text(f"ALTER SEQUENCE {seq} RESTART WITH 1")
            )
        
        await session.commit()
        print(f"Reset {len(sequences)} sequences to 1")

if __name__ == "__main__":
    asyncio.run(reset_sequences())
