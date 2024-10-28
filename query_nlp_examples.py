"""
Examples of common NLP result queries.
"""

import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.text_line import TextLine

async def show_nlp_examples():
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
        # Example 1: Find lines by lemma
        print("\nExample 1: Find lines containing lemma 'νόσος' (disease)")
        stmt = select(TextLine).where(
            func.jsonb_path_exists(
                TextLine.spacy_tokens,
                '$.tokens[*] ? (@.lemma == "νόσος")'
            )
        )
        result = await session.execute(stmt)
        lines = result.scalars().all()
        for line in lines[:3]:  # Show first 3 results
            print(f"Line: {line.content}")
            
        # Example 2: Find lines by part of speech
        print("\nExample 2: Find lines with nouns")
        stmt = select(TextLine).where(
            func.jsonb_path_exists(
                TextLine.spacy_tokens,
                '$.tokens[*] ? (@.pos == "NOUN")'
            )
        )
        result = await session.execute(stmt)
        lines = result.scalars().all()
        for line in lines[:3]:  # Show first 3 results
            print(f"Line: {line.content}")
            # Extract nouns
            nouns = [
                token['text'] 
                for token in line.spacy_tokens['tokens'] 
                if token['pos'] == 'NOUN'
            ]
            print(f"Nouns: {nouns}")
            
        # Example 3: Find lines by multiple categories
        print("\nExample 3: Find lines with both MEDICAL and BODY categories")
        stmt = select(TextLine).where(
            TextLine.categories.contains(['MEDICAL', 'BODY'])
        )
        result = await session.execute(stmt)
        lines = result.scalars().all()
        for line in lines[:3]:  # Show first 3 results
            print(f"Line: {line.content}")
            print(f"Categories: {line.categories}")
            
        # Example 4: Get token analysis
        print("\nExample 4: Detailed token analysis for a line")
        stmt = select(TextLine).limit(1)  # Get any line
        result = await session.execute(stmt)
        line = result.scalar_one_or_none()
        if line and line.spacy_tokens:
            print(f"Line: {line.content}")
            for token in line.spacy_tokens['tokens']:
                print(f"""
Token: {token['text']}
  Lemma: {token['lemma']}
  POS: {token['pos']}
  Tag: {token['tag']}
  Dep: {token['dep']}
  Morph: {token['morph']}
  Category: {token['category']}
""")

if __name__ == "__main__":
    asyncio.run(show_nlp_examples())
