"""
Test script for NLP query examples.
Tests various query patterns for searching spacy_tokens.
"""

import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_lemma_search():
    """Test searching for lemmas in spacy_tokens."""
    async with async_session_maker() as session:
        # Example lemma search query
        query = text("""
            WITH matched_lines AS (
        SELECT DISTINCT ON (tl.id)
            tl.id AS line_id,
            tl.content AS line_text,
            tl.line_number,
            tl.spacy_tokens,
            td.id AS division_id,
            td.author_name,
            td.work_name,
            td.volume,
            td.chapter,
            td.section,
            LAG(tl.content) OVER (
                PARTITION BY td.id
                ORDER BY tl.line_number
            ) AS next_sentence,
                    array_agg(tl.line_number) OVER (
                        PARTITION BY tl.id
                    ) AS line_numbers                
        FROM text_lines tl
        JOIN text_divisions td ON tl.division_id = td.id
        JOIN texts t ON td.text_id = t.id
        WHERE tl.spacy_tokens IS NOT NULL)
            
SELECT * FROM matched_lines;
        """)
        
        try:
            result = await session.execute(query)
            rows = result.mappings().all()
            
            logger.info(f"Found {len(rows)} matches")
            for row in rows:
                    logger.info("---")
                    logger.info(f"Text: {row['title']}")
                    logger.info(f"Citation: [{row['author_name']}] [{row['work_name']}]")
                    if row['prev_line']:
                        logger.info(f"Previous: {row['prev_line']}")
                    logger.info(f"Current:  {row['content']}")
                    if row['next_line']:
                        logger.info(f"Next:     {row['next_line']}")
            
            except Exception as e:
                logger.error(f"Query error: {str(e)}")
                raise

async def test_category_search():
    """Test searching for categories in spacy_tokens."""
    async with async_session_maker() as session:
        # Example category search query with proper type casting
        query = text("""
            SELECT DISTINCT 
                tl.content,
                td.author_id_field,
                td.work_number_field,
                t.title
            FROM text_lines tl
            JOIN text_divisions td ON tl.division_id = td.id
            JOIN texts t ON td.text_id = t.id
            WHERE tl.categories @> ARRAY[:category]
            ORDER BY t.title, td.author_id_field;
        """)
        
        try:
            result = await session.execute(
                query,
                {"category": "Adjectives/Qualities"}
            )
            rows = result.mappings().all()
            
            logger.info(f"Found {len(rows)} matches")
            for row in rows:
                logger.info("---")
                logger.info(f"Text: {row['title']}")
                logger.info(f"Citation: [{row['author_id_field']}] [{row['work_number_field']}]")
                logger.info(f"Content: {row['content']}")
        
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise

async def test_token_category_search():
    """Test searching for categories in spacy_tokens tokens array."""
    async with async_session_maker() as session:
        # Example token category search query
        query = text("""
            SELECT DISTINCT 
                tl.content,
                td.author_id_field,
                td.work_number_field,
                t.title
            FROM text_lines tl
            JOIN text_divisions td ON tl.division_id = td.id
            JOIN texts t ON td.text_id = t.id
            WHERE CAST(tl.spacy_tokens AS TEXT) ILIKE :pattern
            ORDER BY t.title, td.author_id_field;
        """)
        
        try:
            result = await session.execute(
                query,
                {"pattern": '%"category":"Adjectives/Qualities"%'}
            )
            rows = result.mappings().all()
            
            logger.info(f"Found {len(rows)} matches")
            for row in rows:
                logger.info("---")
                logger.info(f"Text: {row['title']}")
                logger.info(f"Citation: [{row['author_id_field']}] [{row['work_number_field']}]")
                logger.info(f"Content: {row['content']}")
        
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise

async def main():
    """Run all test queries."""
    try:
        logger.info("Testing lemma search...")
        await test_lemma_search()
        
        logger.info("\nTesting category search (using categories array)...")
        await test_category_search()
        
        logger.info("\nTesting category search (using spacy_tokens)...")
        await test_token_category_search()
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
