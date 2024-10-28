"""Test script to verify UUID migration for lemmas and analyses."""

from app.core.database import async_session_maker
import asyncio
from sqlalchemy import select
from app.models.lemma import Lemma
from app.models.lemma_analysis import LemmaAnalysis
from sqlalchemy.orm import selectinload

async def test_uuid_relationships():
    """Create a test lemma and analysis to verify UUID relationships."""
    async with async_session_maker() as session:
        # Create a test lemma
        test_lemma = Lemma(
            lemma="δοκιμή",  # "test" in Ancient Greek
            language_code="grc",
            categories=["test"],
            translations={"en": "test"}
        )
        session.add(test_lemma)
        await session.flush()
        
        # Create a test analysis
        test_analysis = LemmaAnalysis(
            lemma_id=test_lemma.id,
            analysis_text="Test analysis for UUID migration verification",
            created_by="migration_test"
        )
        session.add(test_analysis)
        
        # Commit the changes
        await session.commit()
        
        # Verify the relationship
        print("\n=== Test Results ===")
        print(f"Created Lemma UUID: {test_lemma.id}")
        print(f"Created Analysis UUID: {test_analysis.id}")
        print(f"Analysis lemma_id: {test_analysis.lemma_id}")
        print(f"Relationship match: {test_lemma.id == test_analysis.lemma_id}")
        
        # Verify bidirectional relationship by loading explicitly
        stmt = select(Lemma).options(selectinload(Lemma.analyses)).where(Lemma.id == test_lemma.id)
        result = await session.execute(stmt)
        loaded_lemma = result.scalar_one()
        
        print("\nVerifying bidirectional relationship:")
        print(f"Lemma analyses count: {len(loaded_lemma.analyses)}")
        if loaded_lemma.analyses:
            print(f"First analysis ID matches: {loaded_lemma.analyses[0].id == test_analysis.id}")
        
        # Clean up
        await session.delete(test_lemma)  # This should cascade delete the analysis
        await session.commit()

if __name__ == "__main__":
    asyncio.run(test_uuid_relationships())
