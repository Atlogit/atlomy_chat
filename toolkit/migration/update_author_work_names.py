"""
Script to update text_divisions, authors, and texts with names from TLG indexes.
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
    """Update text_divisions, authors, and texts with names from TLG indexes."""
    try:
        # Load indexes
        tlg_index, work_numbers = await load_indexes()
        
        # Create async engine using the standard DATABASE_URL
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT
        )
        
        async with engine.begin() as conn:
            # Get all distinct author/work combinations
            query = """
            SELECT DISTINCT author_id_field, work_number_field 
            FROM text_divisions
            """
            result = await conn.execute(text(query))
            rows = result.fetchall()
            
            logger.info(f"Found {len(rows)} unique author/work combinations to process")
            
            divisions_updated = 0
            authors_updated = 0
            texts_updated = 0
            
            for author_id_field, work_number_field in rows:
                # Get names from indexes
                author_name = tlg_index.get(f"TLG{author_id_field}", "Unknown Author")
                work_name = work_numbers.get(author_id_field, {}).get(work_number_field, "Unknown Work")
                
                # Update text_divisions
                update_divisions_query = """
                UPDATE text_divisions 
                SET author_name = :author_name, work_name = :work_name
                WHERE author_id_field = :author_id_field 
                AND work_number_field = :work_number_field
                AND (author_name != :author_name OR work_name != :work_name)
                RETURNING id
                """
                result = await conn.execute(
                    text(update_divisions_query),
                    {
                        "author_name": author_name,
                        "work_name": work_name,
                        "author_id_field": author_id_field,
                        "work_number_field": work_number_field
                    }
                )
                updated_count = len(result.fetchall())
                divisions_updated += updated_count
                if updated_count > 0:
                    logger.info(f"Updated {updated_count} text_divisions for author {author_id_field} work {work_number_field}")

                # Update author record - using same pattern as text_divisions
                update_author_query = """
                UPDATE authors 
                SET name = :author_name,
                    normalized_name = :author_name
                WHERE reference_code = :author_id_field
                AND (name != :author_name OR normalized_name != :author_name)
                RETURNING id
                """
                result = await conn.execute(
                    text(update_author_query),
                    {
                        "author_name": author_name,
                        "author_id_field": author_id_field
                    }
                )
                updated_count = len(result.fetchall())
                authors_updated += updated_count
                if updated_count > 0:
                    logger.info(f"Updated author {author_id_field} with name '{author_name}'")

                # Update text record - using same pattern as text_divisions
                update_text_query = """
                UPDATE texts 
                SET title = :work_name
                FROM authors
                WHERE texts.author_id = authors.id
                AND authors.reference_code = :author_id_field
                AND texts.reference_code = :work_number_field
                AND texts.title != :work_name
                RETURNING texts.id
                """
                result = await conn.execute(
                    text(update_text_query),
                    {
                        "work_name": work_name,
                        "author_id_field": author_id_field,
                        "work_number_field": work_number_field
                    }
                )
                updated_count = len(result.fetchall())
                texts_updated += updated_count
                if updated_count > 0:
                    logger.info(f"Updated text {work_number_field} with title '{work_name}'")
        
        logger.info(f"""
        Update Summary:
        - Text Divisions updated: {divisions_updated}
        - Authors updated: {authors_updated}
        - Texts updated: {texts_updated}
        """)
        
    except Exception as e:
        logger.error(f"Error updating names: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(update_names())
