"""
Script to demonstrate accessing NLP results from the database.
"""

import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine

def format_expected_nlp_data(text):
    """Show what the NLP data should look like for a given text."""
    return {
        "text": text,
        "tokens": [
            {
                "text": token,
                "lemma": "lemma form",
                "pos": "POS tag",
                "tag": "detailed tag",
                "dep": "dependency",
                "morph": "morphology",
                "category": "detected category"
            }
            for token in text.split()
        ]
    }

async def main():
    # Create async engine
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost/amta_greek",
        echo=False
    )
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Get database statistics
        stmt = select(
            func.count().label('total'),
            func.count(TextLine.spacy_tokens).label('with_tokens'),
            func.count(TextLine.categories).label('with_categories')
        ).select_from(TextLine)
        result = await session.execute(stmt)
        stats = result.one()
        print("\nDatabase Statistics:")
        print(f"Total lines: {stats.total}")
        print(f"Lines with spacy_tokens: {stats.with_tokens}")
        print(f"Lines with categories: {stats.with_categories}")
        
        # Sample some lines
        stmt = select(TextLine).limit(3)
        result = await session.execute(stmt)
        lines = result.scalars().all()
        
        print("\nCurrent Data Structure:")
        for line in lines:
            print(f"\nLine: {line.content}")
            print(f"Categories: {line.categories}")
            print(f"Current spacy_tokens: {line.spacy_tokens}")
            
        print("\nExpected Data Structure:")
        for line in lines:
            print(f"\nLine: {line.content}")
            print(f"Categories: {line.categories}")
            print("Expected spacy_tokens:")
            print(format_expected_nlp_data(line.content))

if __name__ == "__main__":
    asyncio.run(main())
