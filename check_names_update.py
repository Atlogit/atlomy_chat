"""
Script to check the results of the author and work names update.
"""

import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker

async def check_names():
    async with async_session_maker() as session:
        # Check for NULL values
        null_query = """
        SELECT COUNT(*) 
        FROM text_divisions 
        WHERE author_name IS NULL OR work_name IS NULL;
        """
        result = await session.execute(text(null_query))
        null_count = result.scalar()
        print(f"Records with NULL names: {null_count}")

        # Sample of updated records
        sample_query = """
        SELECT author_id_field, work_number_field, author_name, work_name 
        FROM text_divisions 
        LIMIT 5;
        """
        result = await session.execute(text(sample_query))
        rows = result.fetchall()
        
        print("\nSample of updated records:")
        for row in rows:
            print(f"Author ID: {row[0]}, Work ID: {row[1]}")
            print(f"Author Name: {row[2]}")
            print(f"Work Name: {row[3]}")
            print("---")

if __name__ == "__main__":
    asyncio.run(check_names())
