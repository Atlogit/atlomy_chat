import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from toolkit.migration.citation_migrator import CitationMigrator
from app.models.text_division import TextDivision
from app.models.text_line import TextLine

async def test_title_migration():
    """Test migration of various title formats."""
    # Test data with different title formats
    test_data = """[0627][050][][]

.t.1 {ΠΕΡΙ ΕΥΣΧΗΜΟΣΥΝΗΣ.}
.1.1 First line of text
.1.2 Second line of text

[0627][013][][]

..t. <ΟΡΚΟΣ.>
..1 First line
..2 Second line

[0086][023][][]

.847a.t. <ΜΗΧΑΝΙΚΑ.>
.847a.11 First line
.847a.12 Second line
"""

    # Create test file
    test_file = Path("test_title.txt")
    test_file.write_text(test_data)

    try:
        # Initialize database connection
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Run migration
            migrator = CitationMigrator(session)
            await migrator.process_text_file(test_file)
            await session.commit()

            # Verify results
            # 1. Check title divisions
            stmt = select(TextDivision).where(TextDivision.is_title == True)
            result = await session.execute(stmt)
            title_divisions = result.scalars().all()

            print("\nTitle Divisions:")
            for div in title_divisions:
                print(f"\nDivision ID: {div.id}")
                print(f"Title Number: {div.title_number}")
                print(f"Section: {div.section}")
                
                # Get the title line
                stmt = select(TextLine).where(TextLine.division_id == div.id)
                result = await session.execute(stmt)
                lines = result.scalars().all()
                for line in lines:
                    print(f"Content: {line.content}")

            # 2. Check regular divisions
            stmt = select(TextDivision).where(TextDivision.is_title == False)
            result = await session.execute(stmt)
            regular_divisions = result.scalars().all()

            print("\nRegular Divisions:")
            for div in regular_divisions:
                print(f"\nDivision ID: {div.id}")
                print(f"Section: {div.section}")
                
                # Get the lines
                stmt = select(TextLine).where(TextLine.division_id == div.id)
                result = await session.execute(stmt)
                lines = result.scalars().all()
                for line in lines:
                    print(f"Line {line.line_number}: {line.content}")

    finally:
        # Cleanup
        test_file.unlink()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_title_migration())
