"""
Test fixtures for the Analysis Application.
"""

import pytest
from typing import Dict, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.lemma import Lemma
from app.models.lemma_analysis import LemmaAnalysis

# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL + "_test"

# Create test engine
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a clean database session for a test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def sample_author(db_session: AsyncSession) -> Author:
    """Create a sample author."""
    author = Author(
        name="Hippocrates",
        normalized_name="hippocrates",
        language_code="grc"
    )
    db_session.add(author)
    await db_session.commit()
    return author

@pytest.fixture
async def sample_text(db_session: AsyncSession, sample_author: Author) -> Text:
    """Create a sample text."""
    text = Text(
        author_id=sample_author.id,
        title="On Sacred Disease",
        reference_code="0057",
        text_metadata={"genre": "medical", "period": "classical"}
    )
    db_session.add(text)
    await db_session.commit()
    return text

@pytest.fixture
async def sample_division(db_session: AsyncSession, sample_text: Text) -> TextDivision:
    """Create a sample text division."""
    division = TextDivision(
        text_id=sample_text.id,
        book_level_1="1",
        chapter="1",
        section="1"
    )
    db_session.add(division)
    await db_session.commit()
    return division

@pytest.fixture
async def sample_lines(db_session: AsyncSession, sample_division: TextDivision) -> List[TextLine]:
    """Create sample text lines with NLP data."""
    lines = [
        TextLine(
            division_id=sample_division.id,
            line_number=1,
            content="περὶ μὲν τῆς ἱερῆς νούσου καλεομένης ὧδ᾽ ἔχει.",
            categories=["disease", "sacred"],
            spacy_tokens={
                "lemmas": ["περί", "μέν", "ὁ", "ἱερός", "νόσος", "καλέω", "ὧδε", "ἔχω"],
                "pos": ["ADP", "PART", "DET", "ADJ", "NOUN", "VERB", "ADV", "VERB"]
            }
        ),
        TextLine(
            division_id=sample_division.id,
            line_number=2,
            content="οὐδέν τί μοι δοκεῖ τῶν ἄλλων θειοτέρη εἶναι νούσων οὐδὲ ἱερωτέρη",
            categories=["disease", "divine"],
            spacy_tokens={
                "lemmas": ["οὐδείς", "τις", "ἐγώ", "δοκέω", "ὁ", "ἄλλος", "θεῖος", "εἰμί", "νόσος", "οὐδέ", "ἱερός"],
                "pos": ["PRON", "PRON", "PRON", "VERB", "DET", "ADJ", "ADJ", "VERB", "NOUN", "CCONJ", "ADJ"]
            }
        )
    ]
    for line in lines:
        db_session.add(line)
    await db_session.commit()
    return lines

@pytest.fixture
async def sample_lemma(db_session: AsyncSession) -> Lemma:
    """Create a sample lemma."""
    lemma = Lemma(
        lemma="νόσος",
        language_code="grc",
        categories=["medical", "disease"],
        translations={
            "en": "disease, sickness",
            "de": "Krankheit",
            "fr": "maladie"
        }
    )
    db_session.add(lemma)
    await db_session.commit()
    return lemma

@pytest.fixture
async def sample_analysis(db_session: AsyncSession, sample_lemma: Lemma) -> LemmaAnalysis:
    """Create a sample lemma analysis."""
    analysis = LemmaAnalysis(
        lemma_id=sample_lemma.id,
        analysis_text="The term νόσος is a fundamental concept in ancient Greek medicine...",
        analysis_data={
            "key_concepts": ["disease", "illness", "medical condition"],
            "usage_patterns": ["general term", "specific conditions"]
        },
        citations={
            "primary": ["Hippocrates, Sacred Disease 1.1", "Galen, Method of Medicine 1.2"],
            "secondary": ["LSJ s.v. νόσος"]
        },
        created_by="test_user"
    )
    db_session.add(analysis)
    await db_session.commit()
    return analysis
