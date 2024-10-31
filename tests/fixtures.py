"""
Test fixtures for the Analysis Application.
"""

import pytest
import uuid
from typing import Dict, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.sentence import Sentence
from app.models.lexical_value import LexicalValue

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
        metadata={"genre": "medical", "period": "classical"}
    )
    db_session.add(text)
    await db_session.commit()
    return text

@pytest.fixture
async def sample_division(db_session: AsyncSession, sample_text: Text) -> TextDivision:
    """Create a sample text division."""
    division = TextDivision(
        text_id=sample_text.id,
        author_id_field="0057",
        work_number_field="001",
        author_name="Hippocrates",
        work_name="De Morbis Sacris",
        epithet_field="Morb.Sacr.",
        volume="1",
        chapter="1",
        section="1",
        division_metadata={"type": "treatise"}
    )
    db_session.add(division)
    await db_session.commit()
    return division

@pytest.fixture
async def sample_sentences(db_session: AsyncSession) -> List[Sentence]:
    """Create sample sentences including one that spans multiple lines and multiple in one line."""
    # First sentence - spans two lines
    sentence1 = Sentence(
        id=uuid.uuid4(),
        content="περὶ μὲν τῆς ἱερῆς νούσου καλεομένης",
        source_line_ids=[1, 2],  # Spans two lines
        start_position=0,
        end_position=30,
        spacy_data={
            "tokens": [
                {"text": "περί", "lemma": "περί", "pos": "ADP"},
                {"text": "νούσου", "lemma": "νόσος", "pos": "NOUN"}
            ]
        },
        categories=["disease", "sacred"]
    )
    
    # Second and third sentences - both in the same line
    sentence2 = Sentence(
        id=uuid.uuid4(),
        content="ὧδ᾽ ἔχει.",
        source_line_ids=[2],  # Same line as end of sentence1
        start_position=31,
        end_position=40,
        spacy_data={
            "tokens": [
                {"text": "ὧδ᾽", "lemma": "ὧδε", "pos": "ADV"},
                {"text": "ἔχει", "lemma": "ἔχω", "pos": "VERB"}
            ]
        },
        categories=["statement"]
    )
    
    sentence3 = Sentence(
        id=uuid.uuid4(),
        content="τὸ πρᾶγμα οὕτως.",
        source_line_ids=[2],  # Same line as sentence2
        start_position=41,
        end_position=55,
        spacy_data={
            "tokens": [
                {"text": "πρᾶγμα", "lemma": "πρᾶγμα", "pos": "NOUN"},
                {"text": "οὕτως", "lemma": "οὕτως", "pos": "ADV"}
            ]
        },
        categories=["statement"]
    )
    
    db_session.add_all([sentence1, sentence2, sentence3])
    await db_session.commit()
    return [sentence1, sentence2, sentence3]

@pytest.fixture
async def sample_text_lines(
    db_session: AsyncSession,
    sample_division: TextDivision,
    sample_sentences: List[Sentence]
) -> List[TextLine]:
    """Create sample text lines demonstrating multiple sentences per line and sentences spanning lines."""
    # First line - contains start of first sentence
    text_line1 = TextLine(
        division_id=sample_division.id,
        sentence_id=sample_sentences[0].id,  # References first sentence
        line_number=1,
        content="περὶ μὲν τῆς ἱερῆς",
        categories=["disease", "sacred"],
        spacy_tokens={
            "tokens": [
                {"text": "περί", "lemma": "περί", "pos": "ADP"},
                {"text": "ἱερῆς", "lemma": "ἱερός", "pos": "ADJ"}
            ]
        }
    )
    
    # Second line - contains end of first sentence and two complete sentences
    text_line2 = TextLine(
        division_id=sample_division.id,
        sentence_id=sample_sentences[0].id,  # References first sentence
        line_number=2,
        content="νούσου καλεομένης. ὧδ᾽ ἔχει. τὸ πρᾶγμα οὕτως.",
        categories=["disease", "statement"],
        spacy_tokens={
            "tokens": [
                {"text": "νούσου", "lemma": "νόσος", "pos": "NOUN"},
                {"text": "ὧδ᾽", "lemma": "ὧδε", "pos": "ADV"},
                {"text": "πρᾶγμα", "lemma": "πρᾶγμα", "pos": "NOUN"}
            ]
        }
    )
    
    db_session.add_all([text_line1, text_line2])
    await db_session.commit()
    return [text_line1, text_line2]

@pytest.fixture
async def sample_lexical_value(
    db_session: AsyncSession,
    sample_text_lines: List[TextLine],
    sample_sentences: List[Sentence]
) -> LexicalValue:
    """Create a sample lexical value."""
    lexical_value = LexicalValue(
        id=uuid.uuid4(),
        lemma="νόσος",
        translation="disease, sickness",
        short_description="A term for disease or sickness in ancient Greek medical texts.",
        long_description="An extensive analysis of νόσος in ancient Greek medical literature...",
        related_terms=["ἱερός νόσος", "πάθος"],
        citations_used={
            "primary": ["Hippocrates, De Morbis Sacris 1.1"],
            "secondary": ["LSJ s.v. νόσος"]
        },
        references={
            "citations": [
                {
                    "sentence": {
                        "id": str(sample_sentences[0].id),
                        "text": sample_sentences[0].content
                    },
                    "citation": "Hippocrates, De Morbis Sacris 1.1",
                    "context": {
                        "line_id": f"{sample_text_lines[0].id},{sample_text_lines[1].id}",
                        "line_text": f"{sample_text_lines[0].content} {sample_text_lines[1].content}"
                    }
                }
            ],
            "metadata": {
                "search_lemma": True,
                "total_citations": 1
            }
        },
        sentence_contexts={
            str(sample_sentences[0].id): {
                "text": sample_sentences[0].content,
                "prev": None,
                "next": str(sample_sentences[1].id),
                "tokens": sample_text_lines[0].spacy_tokens
            }
        },
        sentence_id=sample_sentences[0].id
    )
    db_session.add(lexical_value)
    await db_session.commit()
    return lexical_value

@pytest.fixture
async def sample_data(
    db_session: AsyncSession,
    sample_author: Author,
    sample_text: Text,
    sample_division: TextDivision,
    sample_sentences: List[Sentence],
    sample_text_lines: List[TextLine],
    sample_lexical_value: LexicalValue
) -> Dict:
    """Create a complete set of sample data."""
    return {
        "author": sample_author,
        "text": sample_text,
        "division": sample_division,
        "sentences": sample_sentences,
        "text_lines": sample_text_lines,
        "lexical_value": sample_lexical_value
    }
