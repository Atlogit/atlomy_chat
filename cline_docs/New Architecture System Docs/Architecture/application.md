# /docs/architecture/application.md
# Analysis Application Architecture

## Purpose
The Analysis Application provides interfaces for searching texts, analyzing terms, and managing lemmas using LLM integration.

## Component Structure

lemma_analysis_app/
├── api/
│ ├── routes/
│ │ ├── texts.py # Text search endpoints
│ │ ├── lemmas.py # Lemma management
│ │ └── analysis.py # LLM analysis
│ └── dependencies.py
├── services/
│ ├── text_service.py # Text retrieval
│ ├── lemma_service.py # Lemma operations
│ ├── analysis_service.py # LLM integration
│ └── search_service.py # Advanced search
└── models/
├── database.py # SQLAlchemy models
└── schemas.py # Pydantic schemas

## Key Features
1. **Text Search**
   - Category-based search (needs expansion to more types)
   - Full-text search
   - Reference lookup
   - Parallel text retrieval

2. **Lemma Management**
   - Creation and editing
   - Category assignment
   - Translation management
   - Reference linking

3. **LLM Analysis**
   - Context gathering
   - Analysis generation
   - Citation linking
   - Result storage

## API Endpoints

### Text Search
```python
@router.get("/texts/search/{category}")
async def search_by_category(
    category: str,
    text_service: TextService = Depends()
):
    return await text_service.find_by_category(category)
```

## Lemma Analysis

```python
@router.post("/analyze/term")
async def analyze_term(
    request: TermAnalysisRequest,
    analysis_service: AnalysisService = Depends()
):
    return await analysis_service.analyze_term(
        request.term,
        request.contexts
    )
```

## Configuration

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4

llm:
  provider: "aws_bedrock"
  model: "claude-3-sonnet"
  max_tokens: 1000

database:
  url: "postgresql+asyncpg://user:pass@localhost/db"
  pool_size: 20

## Next Steps
Review the Database Schema
Understand the Query Patterns
Follow the Implementation Guide

