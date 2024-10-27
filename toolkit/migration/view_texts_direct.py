"""Script to directly view migrated texts and lines from the database."""
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.core.database import async_session
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.author import Author

async def view_texts():
    """View all texts and their lines directly from the database."""
    async with async_session() as session:
        # Query texts with author and all related data
        query = (
            select(Text)
            .options(
                joinedload(Text.author),
                joinedload(Text.divisions).joinedload(TextDivision.lines)
            )
            .order_by(Text.title)
        )
        
        result = await session.execute(query)
        texts = result.unique().scalars().all()
        
        print("\n=== All Texts ===")
        for text in texts:
            print(f"\nTitle: {text.title}")
            print(f"Author: {text.author.name if text.author else 'Unknown'}")
            print(f"Reference: {text.reference_code}")
            
            if text.divisions:
                print("\nContent:")
                for division in text.divisions:
                    sorted_lines = sorted(division.lines, key=lambda x: x.line_number)
                    for line in sorted_lines:
                        print(f"{line.line_number}: {line.content}")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(view_texts())
