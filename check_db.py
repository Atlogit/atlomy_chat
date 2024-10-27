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
            for line in div.lines[:3]:
                print(div)
                print(f"  {line.line_number}: {line.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(check_db())
