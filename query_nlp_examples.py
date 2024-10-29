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
                SELECT 
                    tl.id,
                    tl.content,
                    tl.line_number,
                    td.author_id_field,
                    td.work_number_field,
                    t.title,
                    LAG(tl.content) OVER (PARTITION BY td.id ORDER BY tl.line_number) as prev_line,
                    LEAD(tl.content) OVER (PARTITION BY td.id ORDER BY tl.line_number) as next_line
                FROM text_lines tl
                JOIN text_divisions td ON tl.division_id = td.id
                JOIN texts t ON td.text_id = t.id
                WHERE CAST(tl.spacy_tokens AS TEXT) ILIKE '%"lemma":"θερμός"%'
            )
            SELECT * FROM matched_lines
            WHERE id IS NOT NULL
            ORDER BY work_number_field, line_number;
        """)
        
        try:
            result = await session.execute(query)
            rows = result.mappings().all()
            
            logger.info(f"Found {len(rows)} matches")
            for row in rows:
                logger.info("---")
                logger.info(f"Text: {row['title']}")
                logger.info(f"Citation: [{row['author_id_field']}] [{row['work_number_field']}]")
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
            WITH category_matches AS (
                SELECT DISTINCT 
                    tl.content,
                    td.author_id_field,
                    td.work_number_field,
                    t.title
                FROM text_lines tl
                JOIN text_divisions td ON tl.division_id = td.id
                JOIN texts t ON td.text_id = t.id
                WHERE tl.categories @> ARRAY[CAST(:category AS VARCHAR)]::VARCHAR[]
            )
            SELECT * FROM category_matches
            ORDER BY title, author_id_field;
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
            WITH sentence_matches AS (
                SELECT DISTINCT ON (s.id)
                    s.id as sentence_id,
                    s.content as sentence_text,
                    tl.spacy_tokens as sentence_tokens,
                    tl.id as line_id,
                    tl.content as line_text,
                    tl.line_number,
                    td.id as division_id,
                    td.author_name,
                    td.work_name,
                    td.volume,
                    td.chapter,
                    td.section,
                    LAG(s.content) OVER (
                        PARTITION BY td.id 
                        ORDER BY tl.line_number
                    ) as prev_sentence,
                    LEAD(s.content) OVER (
                        PARTITION BY td.id 
                        ORDER BY tl.line_number
                    ) as next_sentence,
                    array_agg(tl.line_number) OVER (
                        PARTITION BY s.id
                    ) as line_numbers
                FROM sentences s
                JOIN text_lines tl ON s.text_line_id = tl.id
                JOIN text_divisions td ON tl.division_id = td.id
                WHERE tl.categories <> '{}'
            )
            SELECT * FROM sentence_matches
            WHERE array_length(line_numbers, 1) > 0
            ORDER BY division_id, line_number;
        """)
        
        try:
            result = await session.execute(query)
            rows = result.mappings().all()
            
            logger.info(f"Found {len(rows)} matches")
            for row in rows:
                logger.info("---")
                logger.info(f"Author: {row['author_name']}")
                logger.info(f"Work: {row['work_name']}")
                logger.info(f"Location: {row['chapter'] or ''} {row['section'] or ''}")
                logger.info(f"Content: {row['sentence_text']}")
                if row['prev_sentence']:
                    logger.info(f"Previous: {row['prev_sentence']}")
                if row['next_sentence']:
                    logger.info(f"Next: {row['next_sentence']}")
        
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise

async def main():
    """Run all test queries."""
    try:
        logger.info("\nTesting category search (using spacy_tokens)...")
        await test_token_category_search()
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
