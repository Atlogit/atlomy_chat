"""
Test configuration and fixtures for the migration toolkit.
"""

import pytest
from pytest_asyncio import fixture
import asyncio
from typing import AsyncGenerator
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import asyncpg

# Import Base from models
from app.models import Base

# Test database URL - using PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/test_ancient_texts"
)

# Create async engine for testing
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=True  # Set to False to reduce log output
)

# Bind engine to metadata
Base.metadata.bind = engine

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop_policy():
    """Create and set an event loop policy for the test session."""
    policy = asyncio.get_event_loop_policy()
    return policy

@pytest.fixture(scope="session")
def event_loop(event_loop_policy):
    """Create an instance of the default event loop for each test case."""
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()

@fixture(scope="session")
async def setup_database():
    """Set up the test database."""
    # Create test database if it doesn't exist
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='postgres',
            database='postgres',
            host='localhost'
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            'test_ancient_texts'
        )
        
        if not exists:
            # Close connections to postgres db before creating new db
            await conn.close()
            
            # Reconnect with autocommit to create database
            sys_conn = await asyncpg.connect(
                user='postgres',
                password='postgres',
                database='postgres',
                host='localhost'
            )
            await sys_conn.execute('CREATE DATABASE test_ancient_texts')
            await sys_conn.close()
        else:
            await conn.close()
            
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise
    
    # Import all models to ensure they're registered with metadata
    from app.models.text import Text
    from app.models.text_division import TextDivision
    from app.models.text_line import TextLine
    from app.models.author import Author
    from app.models.lemma import Lemma
    from app.models.lemma_analysis import LemmaAnalysis
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Cleanup after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@fixture
async def db_session() -> AsyncSession:
    """Create a new database session for a test."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@fixture
async def large_dataset(db_session: AsyncSession):
    """Create a large dataset for integration testing."""
    from app.models.text import Text
    from app.models.text_division import TextDivision
    from app.models.text_line import TextLine
    
    # Create multiple texts
    texts = []
    for i in range(5):  # 5 texts
        text = Text(
            title=f"Large Text {i+1}",
            text_metadata={"source": "integration_test"}
        )
        db_session.add(text)
        texts.append(text)
    
    await db_session.flush()
    
    # Create many divisions per text
    divisions = []
    for text in texts:
        for i in range(20):  # 20 divisions per text
            division = TextDivision(
                text_id=text.id,
                book_number=str(i+1),
                metadata={"test_data": True}
            )
            db_session.add(division)
            divisions.append(division)
    
    await db_session.flush()
    
    # Create many lines per division with substantial content
    sample_texts = [
        "Ἱπποκράτης μὲν οὖν, ὥσπερ καὶ ἄλλα πολλὰ καλῶς ἀπεφήνατο",
        "τὸ γὰρ ἐν τῇ κεφαλῇ ἐγκέφαλον πρῶτον μὲν τῶν κατὰ τὸν ἄνθρωπον ψυχρότατον",
        "διὸ καὶ τὴν χολὴν ξανθὴν εἶναί φησι θερμήν",
        "ταῦτα μὲν οὖν Ἱπποκράτης ὀρθῶς ἀπεφήνατο περὶ τῆς τῶν χυμῶν φύσεως"
    ]
    
    for division in divisions:
        for i in range(50):  # 50 lines per division
            line = TextLine(
                division_id=division.id,
                content=sample_texts[i % len(sample_texts)],
                line_number=i+1
            )
            db_session.add(line)
    
    await db_session.commit()
    return texts, divisions

@pytest.fixture(scope="session")
def nlp_model():
    """Load spaCy model for testing."""
    import spacy
    
    # Use a small model for testing
    try:
        nlp = spacy.load("xx_ent_wiki_sm")
    except OSError:
        # Download if not available
        spacy.cli.download("xx_ent_wiki_sm")
        nlp = spacy.load("xx_ent_wiki_sm")
    
    return nlp

@fixture(autouse=True)
async def setup_test_env(setup_database):
    """Automatically set up test environment for all tests."""
    yield

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Additional test utilities
@pytest.fixture
def sample_greek_texts():
    """Provide sample Greek texts for testing."""
    return {
        "basic": "Τὸ σῶμα τοῦ ἀνθρώπου ἔχει ὀστέα· καὶ νεῦρα καὶ σάρκας.",
        "multi_sentence": (
            "ἡ κεφαλὴ ἔχει ἐγκέφαλον. "
            "τὸ στῆθος ἔχει καρδίαν· "
            "ἡ γαστὴρ ἔχει ἧπαρ καὶ σπλῆνα."
        ),
        "complex": (
            "περὶ δὲ τῆς ἱερῆς νούσου καλεομένης ὧδε ἔχει· "
            "οὐδέν τί μοι δοκέει τῶν ἄλλων θειοτέρη εἶναι νούσων οὐδὲ ἱερωτέρη· "
            "ἀλλὰ φύσιν μὲν ἔχει καὶ πρόφασιν."
        )
    }

@pytest.fixture
def mock_nlp_pipeline():
    """Create a mock NLP pipeline for testing."""
    class MockNLPPipeline:
        def process_text(self, text):
            return {
                "text": text,
                "tokens": [
                    {
                        "text": token,
                        "lemma": token.lower(),
                        "pos": "NOUN",
                        "tag": "NN",
                        "dep": "nsubj",
                        "morph": "",
                        "category": ["BODY"] if "σῶμα" in token else []
                    }
                    for token in text.split()
                ]
            }
        
        def process_batch(self, texts):
            return [self.process_text(text) for text in texts]
        
        def extract_categories(self, processed_text):
            categories = []
            for token in processed_text["tokens"]:
                categories.extend(token.get("category", []))
            return list(set(categories))
    
    return MockNLPPipeline()

@pytest.fixture
def mock_progress_tracker():
    """Create a mock progress tracker for testing."""
    from tqdm import tqdm
    
    class MockProgressBar:
        def __init__(self, *args, **kwargs):
            self.n = 0
            self.total = kwargs.get('total', 100)
        
        def update(self, n=1):
            self.n += n
        
        def close(self):
            pass
    
    return lambda *args, **kwargs: MockProgressBar(*args, **kwargs)
