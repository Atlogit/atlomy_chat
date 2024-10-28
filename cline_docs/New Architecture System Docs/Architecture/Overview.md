# /docs/architecture/overview.md
# System Architecture Overview

## Current Systems
The project integrates three existing systems:

1. **Coda Tables**
   - Parallel early/modern references
   - Multiple translations
   - Rich metadata structure

2. **Atlomy.com (Elasticsearch)**
   - Nested document structure
   - Multi-language support
   - Complex reference system

3. **Processing Pipeline**
   - spaCy NLP analysis
   - Citation parsing ([0057] format)
   - AWS Bedrock (Claude-3) integration

## New Architecture
The system is being split into two main components:

1. **[Text Processing Toolkit](toolkit.md)**
   - Handles text ingestion
   - Processes NLP analysis
   - Manages database population
   - [Sentence Processing Flow](../sentence_processing_flow.md) - Advanced handling of multi-line sentences and token mapping

2. **[Analysis Application](application.md)**
   - Provides text search and analysis
   - Manages lemma creation
   - Integrates with LLM for analysis

## System Interaction Diagram

[Text Files] → [Text Processing Toolkit] → [Database] ← [Analysis Application] ← [Users]
↓ ↑ ↓
[NLP Processing] [Elasticsearch] [AWS Bedrock]

## Key Components
- PostgreSQL Database (shared resource)
- FastAPI Backend
- AWS Bedrock Integration
- spaCy NLP Pipeline
- Advanced Sentence Processing System

## Technology Stack
- Python 3.9+
- FastAPI
- PostgreSQL 14+
- SQLAlchemy 2.0
- spaCy
- AWS Bedrock
- Alembic

## Next Steps
- Review the [Toolkit Architecture](toolkit.md)
- Review the [Application Architecture](application.md)
- Understand the [Database Schema](../database/schema.md)
- Study the [Sentence Processing Flow](../sentence_processing_flow.md)


I'll create documentation focused on restructuring the existing codebase into the new architecture.

```markdown
# /docs/restructuring/overview.md
# Code Restructuring Guide

## Current to New Architecture Migration

### Current Structure
```
existing_project/
├── indexutils.py         # Citation handling
├── documents.py          # Elasticsearch models
└── processing scripts    # Various text processing
```

### Target Structure
```
ancient_texts/
├── text_processing_toolkit/    # Toolkit for processing
└── lemma_analysis_app/        # Main application
```

## Separation Strategy

1. **Text Processing Toolkit**
   - One-time/occasional use
   - Text processing utilities
   - Database population
   - Advanced sentence processing

2. **Lemma Analysis Application**
   - Regular interactive use
   - Text search and analysis
   - LLM integration
```

```markdown
# /docs/restructuring/toolkit_setup.md
# Text Processing Toolkit Setup

## 1. Create Toolkit Structure
```bash
mkdir text_processing_toolkit
cd text_processing_toolkit

# Create package structure
mkdir -p {processors,importers,db,utils}
touch __init__.py
```

## 2. Move Existing Code

### Citation Parser
```python
# text_processing_toolkit/processors/citation_parser.py
# Move from indexutils.py

class CitationParser:
    def __init__(self, tlg_index_path=None):
        self.logger = get_logger()
        self.tlg_index = self._load_index(tlg_index_path)

    async def process_citations(self, text: str) -> str:
        """Process [0057] style citations in text."""
        # Move existing citation processing logic here
```

### Text Processor
```python
# text_processing_toolkit/processors/text_processor.py

class TextProcessor:
    def __init__(self, nlp_model=None):
        self.nlp = nlp_model or load_default_model()
        self.citation_parser = CitationParser()

    async def process_text(self, text: str) -> dict:
        """Process text through pipeline."""
        # 1. Clean text
        cleaned = self.clean_text(text)
        
        # 2. Process citations
        with_citations = await self.citation_parser.process_citations(cleaned)
        
        # 3. Run NLP
        doc = self.nlp(with_citations)
        
        return {
            'text': with_citations,
            'nlp_data': self.extract_nlp_data(doc)
        }
```

## 3. Database Integration

### Models
```python
# text_processing_toolkit/db/models.py

from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProcessedText(Base):
    __tablename__ = 'processed_texts'
    
    id = Column(Integer, primary_key=True)
    content = Column(String)
    nlp_data = Column(JSON)
    citations = Column(JSON)
```

### Database Operations
```python
# text_processing_toolkit/db/operations.py

class DatabaseLoader:
    def __init__(self, session):
        self.session = session

    async def store_processed_text(self, processed: dict):
        text_entry = ProcessedText(
            content=processed['text'],
            nlp_data=processed['nlp_data']
        )
        self.session.add(text_entry)
        await self.session.commit()
```

## 4. Main Processing Pipeline
```python
# text_processing_toolkit/pipeline.py

class ProcessingPipeline:
    def __init__(self, db_session):
        self.text_processor = TextProcessor()
        self.db_loader = DatabaseLoader(db_session)

    async def process_file(self, file_path: str):
        # 1. Read file
        text = await self.read_file(file_path)
        
        # 2. Process text
        processed = await self.text_processor.process_text(text)
        
        # 3. Store results
        await self.db_loader.store_processed_text(processed)
```

## Usage Example
```python
# example_usage.py

async def process_new_text():
    # Setup
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        pipeline = ProcessingPipeline(session)
        await pipeline.process_file("new_text.txt")
```
```

```markdown
# /docs/restructuring/app_setup.md
# Lemma Analysis Application Setup

## 1. Create Application Structure
```bash
mkdir lemma_analysis_app
cd lemma_analysis_app

# Create package structure
mkdir -p {api,services,models}
touch __init__.py
```

## 2. Setup API Components

### FastAPI Application
```python
# lemma_analysis_app/api/app.py

from fastapi import FastAPI
from .routes import texts, analysis

app = FastAPI(title="Lemma Analysis API")

app.include_router(texts.router, prefix="/texts", tags=["texts"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
```

### Text Routes
```python
# lemma_analysis_app/api/routes/texts.py

from fastapi import APIRouter, Depends
from ..services.text_service import TextService

router = APIRouter()

@router.get("/search/{category}")
async def search_texts(
    category: str,
    text_service: TextService = Depends()
):
    return await text_service.find_by_category(category)
```

## 3. Services Layer

### Text Service
```python
# lemma_analysis_app/services/text_service.py

class TextService:
    def __init__(self, db_session):
        self.db = db_session

    async def find_by_category(self, category: str):
        query = """
        SELECT content, nlp_data
        FROM processed_texts
        WHERE nlp_data->'spans' @> $1
        """
        return await self.db.fetch_all(
            query, 
            {'label': category}
        )
```

### Analysis Service
```python
# lemma_analysis_app/services/analysis_service.py

class AnalysisService:
    def __init__(self, db_session, bedrock_client):
        self.db = db_session
        self.llm = bedrock_client

    async def analyze_term(self, term: str):
        # 1. Gather contexts
        contexts = await self.get_term_contexts(term)
        
        # 2. Generate analysis
        analysis = await self.llm.analyze(term, contexts)
        
        # 3. Store results
        await self.store_analysis(term, analysis)
        
        return analysis
```

## 4. Database Models
```python
# lemma_analysis_app/models/database.py

from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    term = Column(String)
    analysis_data = Column(JSON)
    contexts = Column(JSON)
```

## 5. AWS Bedrock Integration
```python
# lemma_analysis_app/services/llm_service.py

class BedrockService:
    def __init__(self, client):
        self.client = client

    async def analyze(self, term: str, contexts: List[dict]):
        prompt = self.create_analysis_prompt(term, contexts)
        response = await self.client.invoke_model(prompt)
        return self.parse_response(response)
```

## Usage Example
```python
# run.py

from fastapi import FastAPI
from lemma_analysis_app.api.app import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
