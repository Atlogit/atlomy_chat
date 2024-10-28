"""
Database monitoring script for the lexical value system.
Monitors performance, cache efficiency, and data integrity.
"""

import asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import async_session_maker
from app.models.lemma import Lemma
from app.models.lemma_analysis import LemmaAnalysis
from app.models.text_line import TextLine
from app.core.redis import redis_client
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LexicalSystemMonitor:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_spacy_tokens_structure(self):
        """Check the structure of spacy_tokens in the database."""
        logger.info("Checking spacy_tokens structure...")
        
        # Get a sample of text lines with spacy_tokens
        query = text("""
            SELECT id, content, spacy_tokens::text
            FROM text_lines
            WHERE spacy_tokens IS NOT NULL
            LIMIT 5;
        """)
        
        result = await self.session.execute(query)
        rows = result.mappings().all()
        
        for row in rows:
            logger.info(f"Line ID: {row['id']}")
            logger.info(f"Content: {row['content']}")
            logger.info(f"Spacy Tokens: {row['spacy_tokens']}")
            logger.info("---")

async def run_monitoring():
    """Run all monitoring checks."""
    try:
        async with async_session_maker() as session:
            monitor = LexicalSystemMonitor(session)
            await monitor.check_spacy_tokens_structure()
            logger.info("Monitoring completed successfully")
    except Exception as e:
        logger.error(f"Error during monitoring: {str(e)}")
        raise
    finally:
        if 'session' in locals():
            await session.close()

def main():
    """Entry point for the monitoring script."""
    try:
        asyncio.run(run_monitoring())
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
