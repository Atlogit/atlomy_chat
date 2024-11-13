"""Script to verify and update line numbers in the database."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

import asyncio
import logging
import re
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from tqdm import tqdm

logger = logging.getLogger(__name__)

def extract_line_number(content: str) -> int:
    """Extract line number from citation format (e.g., .51.6)."""
    if not content:
        return None
        
    # Look for citation pattern like .51.6
    match = re.search(r'\.\d+\.(\d+)\.', content)
    if match:
        return int(match.group(1))
    return None

async def update_line_numbers(session: AsyncSession) -> None:
    """Update line numbers based on citation information.
    
    This preserves the original line numbers from the text citations
    rather than forcing sequential numbering.
    """
    # Get all divisions
    stmt = select(TextDivision)
    result = await session.execute(stmt)
    divisions = result.scalars().all()
    
    logger.info(f"Processing {len(divisions)} divisions")
    
    for division in tqdm(divisions, desc="Updating line numbers"):
        # Get all lines for this division
        stmt = select(TextLine).where(
            TextLine.division_id == division.id
        ).order_by(TextLine.id)
        result = await session.execute(stmt)
        lines = result.scalars().all()
        
        # Update line numbers based on citation info
        for line in lines:
            citation_line_number = extract_line_number(line.content)
            if citation_line_number and line.line_number != citation_line_number:
                logger.info(
                    f"Updating line number for division {division.id} line {line.id}: "
                    f"{line.line_number} -> {citation_line_number} (from citation)"
                )
                stmt = update(TextLine).where(
                    TextLine.id == line.id
                ).values(line_number=citation_line_number)
                await session.execute(stmt)
        
        await session.flush()

async def main():
    """Main entry point."""
    async with async_session_maker() as session:
        async with session.begin():
            await update_line_numbers(session)
            await session.commit()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
