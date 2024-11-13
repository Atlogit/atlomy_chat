"""
Database reset script for cleaning and reinitializing the database.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from sqlalchemy import text
from db_config import SQLALCHEMY_DATABASE_URL

async def reset_database():
    print("Connecting to database...")
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True
    )
    
    async with engine.begin() as conn:
        print("\nDropping all tables...")
        # Drop all tables with CASCADE to handle dependencies
        await conn.execute(text('DROP SCHEMA public CASCADE'))
        await conn.execute(text('CREATE SCHEMA public'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO public'))

        print("\nCreating all tables...")
        # Check if the table exists before creating it
        for table_name in Base.metadata.tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                print(f"Dropped table: {table_name}")
            except Exception as e:
                print(f"Error dropping table {table_name}: {e}")

        # Recreate the tables
        await conn.run_sync(Base.metadata.create_all)

        # Reset sequences - these are automatically created by PostgreSQL
        print("\nResetting sequences...")
        sequences = [
            "authors_id_seq",
            "texts_id_seq",
            "text_divisions_id_seq",
            "text_lines_id_seq"
        ]
        
        for seq in sequences:
            try:
                await conn.execute(text(f"DROP SEQUENCE IF EXISTS {seq} CASCADE"))
                print(f"Dropped sequence: {seq}")
            except Exception as e:
                print(f"Error resetting sequence {seq}: {e}")

        # Create additional indexes for sentence-related tables
        print("\nCreating additional indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sentences_content ON sentences USING gin (to_tsvector('greek', content))",
            "CREATE INDEX IF NOT EXISTS idx_sentences_categories ON sentences USING gin (categories)"
        ]
        
        for idx in indexes:
            try:
                await conn.execute(text(idx))
                print(f"Created index: {idx}")
            except Exception as e:
                print(f"Error creating index: {e}")

        print("\nDatabase reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_database())
