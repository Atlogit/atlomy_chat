"""Script to verify sentence line numbers for specific examples."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

import asyncio
import logging
from typing import List
from sqlalchemy import select, and_, func
from app.core.database import async_session_maker
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.sentence import sentence_text_lines, Sentence

logger = logging.getLogger(__name__)

async def get_context_lines(session, division_id: int, center_line_number: int, context: int = 2) -> List[TextLine]:
    """Get lines before and after the given line number."""
    stmt = (
        select(TextLine)
        .where(
            and_(
                TextLine.division_id == division_id,
                TextLine.line_number >= center_line_number - context,
                TextLine.line_number <= center_line_number + context
            )
        )
        .order_by(TextLine.line_number)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def verify_sentence(session, chapter: str, lemma: str) -> None:
    """Verify sentence line numbers for a specific example."""
    print(f"\nChecking chapter {chapter} for lemma '{lemma}':")
    
    # First get the division
    stmt = select(TextDivision).where(TextDivision.chapter == chapter)
    result = await session.execute(stmt)
    division = result.scalar_one_or_none()
    
    if not division:
        print(f"No division found for chapter {chapter}")
        return
    
    print(f"Found division: {division.id}")
    
    # Get all sentences with their spacy data
    stmt = select(Sentence)
    result = await session.execute(stmt)
    sentences = result.scalars().all()
    
    matching_sentences = []
    for sentence in sentences:
        # Check if any token in the sentence has the target lemma
        if sentence.spacy_data and 'tokens' in sentence.spacy_data:
            for token in sentence.spacy_data['tokens']:
                if token.get('lemma') == lemma:
                    matching_sentences.append(sentence)
                    break
    
    print(f"Found {len(matching_sentences)} sentences containing lemma '{lemma}'")
    
    for sentence in matching_sentences:
        # Get lines for this sentence
        stmt = (
            select(TextLine)
            .join(sentence_text_lines)
            .where(sentence_text_lines.c.sentence_id == sentence.id)
            .where(TextLine.division_id == division.id)
            .order_by(TextLine.line_number)
        )
        result = await session.execute(stmt)
        sentence_lines = result.scalars().all()
        
        if sentence_lines:
            print(f"\nSentence: {sentence.content}")
            
            # Get context for first and last lines
            first_line = sentence_lines[0]
            last_line = sentence_lines[-1]
            
            print(f"\nContext around line range {first_line.line_number}-{last_line.line_number}:")
            
            # Get context lines for first line
            context_lines = await get_context_lines(session, division.id, first_line.line_number)
            for line in context_lines:
                prefix = ">" if line.line_number in [l.line_number for l in sentence_lines] else " "
                print(f"{prefix} Line {line.line_number}: {line.content}")
                if line.spacy_tokens and 'tokens' in line.spacy_tokens:
                    for token in line.spacy_tokens['tokens']:
                        if token.get('lemma') == lemma:
                            print(f"    Found lemma '{lemma}' in word form: {token['text']}")
            
            # If last line is more than 5 lines after first line, show context around it too
            if last_line.line_number > first_line.line_number + 5:
                print("\n...")
                context_lines = await get_context_lines(session, division.id, last_line.line_number)
                for line in context_lines:
                    prefix = ">" if line.line_number in [l.line_number for l in sentence_lines] else " "
                    print(f"{prefix} Line {line.line_number}: {line.content}")
                    if line.spacy_tokens and 'tokens' in line.spacy_tokens:
                        for token in line.spacy_tokens['tokens']:
                            if token.get('lemma') == lemma:
                                print(f"    Found lemma '{lemma}' in word form: {token['text']}")

async def main():
    """Check specific examples."""
    async with async_session_maker() as session:
        # Example 1: Chapter 51
        await verify_sentence(session, "51", "αὐχήν")
        
        # Example 2: Chapter 57
        await verify_sentence(session, "57", "αὐχήν")
        
        # Example 3: Chapter 55
        await verify_sentence(session, "55", "αὐχήν")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
