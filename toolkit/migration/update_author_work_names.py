"""
Script to update text_divisions with author and work names from TLG indexes.
"""

import asyncio
import importlib.util
from pathlib import Path
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_indexes():
    """Load TLG and works indexes."""
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        authors_path = project_root / "assets" / "indexes" / "tlg_index.py"
        works_path = project_root / "assets" / "indexes" / "work_numbers.py"
        
        # Load TLG index
        spec = importlib.util.spec_from_file_location("tlg_index", authors_path)
        tlg_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tlg_module)
        tlg_index = getattr(tlg_module, 'TLG_INDEX')
        
        # Load works index
        spec = importlib.util.spec_from_file_location("work_numbers", works_path)
        works_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(works_module)
        work_numbers = getattr(works_module, 'TLG_WORKS_INDEX')
        
        logger.info("Successfully loaded TLG and works indexes")
        return tlg_index, work_numbers
    except Exception as e:
        logger.error(f"Failed to load index files: {str(e)}")
        raise

async def update_names():
    """Update text_divisions with author and work names."""
    try:
        # Load indexes
        tlg_index, work_numbers = await load_indexes()
        
        # Create async engine using the standard DATABASE_URL
        # Note: DATABASE_URL already includes the asyncpg driver
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT
        )
        
        async with engine.begin() as conn:
            # Get all text_divisions that need updating
            query = """
            SELECT DISTINCT author_id_field, work_number_field 
            FROM text_divisions 
            WHERE author_name IS NULL OR work_name IS NULL
            """
            result = await conn.execute(text(query))
            rows = result.fetchall()
            
            logger.info(f"Found {len(rows)} unique author/work combinations to update")
            
            for author_id_field, work_number_field in rows:
                # Get names from indexes
                author_name = tlg_index.get(f"TLG{author_id_field}", "Unknown Author")
                work_name = work_numbers.get(author_id_field, {}).get(work_number_field, "Unknown Work")
                
                # Update records
                update_query = """
                UPDATE text_divisions 
                SET author_name = :author_name, work_name = :work_name
                WHERE author_id_field = :author_id_field 
                AND work_number_field = :work_number_field
                """
                await conn.execute(
                    text(update_query),
                    {
                        "author_name": author_name,
                        "work_name": work_name,
                        "author_id_field": author_id_field,
                        "work_number_field": work_number_field
                    }
                )
                
                logger.info(f"Updated records for author {author_id_field} work {work_number_field}")
                logger.info(f"Set author_name to '{author_name}' and work_name to '{work_name}'")
        
        logger.info("Successfully updated all text_divisions with author and work names")
        
    except Exception as e:
        logger.error(f"Error updating names: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(update_names())
