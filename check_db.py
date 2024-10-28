"""
Database inspection script for checking loaded texts and their relationships.
"""

from app.core.database import async_session
import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.text import Text
from app.models.author import Author
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.migration.corpus_processor import CorpusProcessor

async def check_nlp_analysis():
    """Check NLP analysis for a sample line."""
    async with async_session() as session:
        # Get a sample text line with NLP analysis
        stmt = select(TextLine).where(TextLine.spacy_tokens.isnot(None)).limit(1)
        result = await session.execute(stmt)
        line = result.scalar_one_or_none()
        
        if line:
            print("\n=== Sample Line NLP Analysis ===")
            print(f"Line content: {line.content}")
            print(f"Categories: {line.categories}")
            print(f"Spacy tokens tensor shape: {len(line.spacy_tokens) if line.spacy_tokens else 'No tokens'}")
            
            # Get the full sentence context
            processor = CorpusProcessor(session)
            # Get the division this line belongs to
            stmt = select(TextDivision).where(TextDivision.id == line.division_id)
            division = (await session.execute(stmt)).scalar_one()
            
            # Get all sentences in this work
            sentences = await processor.get_work_sentences(division.text_id)
            
            # Find the sentence containing our line
            target_sentence = None
            for sentence in sentences:
                if any(l.content == line.content for l in sentence.source_lines):
                    target_sentence = sentence
                    break
            
            if target_sentence:
                print("\n=== Full Sentence Context ===")
                print(f"Sentence: {target_sentence.content}")
                
                # Get NLP analysis for the sentence
                analysis = await processor.get_sentence_analysis(target_sentence)
                print(f"\nNLP Analysis available: {'Yes' if analysis else 'No'}")
        else:
            print("\nNo lines with NLP analysis found")

async def check_db():
    async with async_session() as session:
        # Get counts
        author_count = await session.scalar(select(func.count(Author.id)))
        text_count = await session.scalar(select(func.count(Text.id)))
        division_count = await session.scalar(select(func.count(TextDivision.id)))
        line_count = await session.scalar(select(func.count(TextLine.id)))
        
        print("\n=== Database Summary ===")
        print(f"Authors: {author_count}")
        print(f"Texts: {text_count}")
        print(f"Divisions: {division_count}")
        print(f"Lines: {line_count}")
        
        # Get authors with their texts
        stmt = select(Author).options(selectinload(Author.texts))
        result = await session.execute(stmt)
        authors = result.scalars().all()
        
        print("\n=== Authors and Their Texts ===")
        for author in authors:
            print(f"\nAuthor: {author.name} (ref: {author.reference_code})")
            for text in author.texts:
                print(f"  - Text: {text.title} (ref: {text.reference_code})")
        
        # Get some sample divisions with their lines
        stmt = select(TextDivision).options(
            selectinload(TextDivision.text),
            selectinload(TextDivision.lines)
        ).limit(3)
        result = await session.execute(stmt)
        divisions = result.scalars().all()
        
        print("\n=== Sample Text Divisions ===")
        for div in divisions:
            print(f"\nDivision in text: {div.text.title}")
            print(f"Citation: [{div.author_id_field}][{div.work_number_field}]"
                  f"{f'[{div.epithet_field}]' if div.epithet_field else ''}"
                  f"{f'[{div.fragment_field}]' if div.fragment_field else ''}")
            print(f"Structure: {div.volume or '-'}.{div.chapter or '-'}.{div.line or '-'}")
            print("First 2 lines:")
            for line in div.lines[:4]:
                print(div)
                print(f"  {line.line_number}: {line.content[:100]}...")

        # Check NLP analysis
        await check_nlp_analysis()

if __name__ == "__main__":
    asyncio.run(check_db())
