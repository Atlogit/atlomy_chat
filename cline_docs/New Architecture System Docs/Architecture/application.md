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
│ │ ├── corpus.py # Citation and search handling
│ │ └── analysis.py # LLM analysis
│ └── dependencies.py
├── services/
│ ├── text_service.py # Text retrieval
│ ├── lemma_service.py # Lemma operations
│ ├── citation_service.py # Citation handling
│ ├── analysis_service.py # LLM integration
│ └── search_service.py # Advanced search
├── models/
│ ├── database.py # SQLAlchemy models
│ ├── citations.py # Citation models
│ └── schemas.py # Pydantic schemas
└── core/
    ├── redis.py # Redis client
    └── config.py # Application config

## Key Features
1. **Text Search**
   - Category-based search with pagination
   - Full-text search with context
   - Reference lookup with citations
   - Parallel text retrieval
   - Redis-based result caching

2. **Citation Management**
   - Efficient chunked storage
   - Paginated result retrieval
   - Citation formatting
   - Context preservation
   - Redis-based caching

3. **Lemma Management**
   - Creation and editing
   - Category assignment
   - Translation management
   - Reference linking

4. **LLM Analysis**
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
    corpus_service: CorpusService = Depends()
) -> SearchResponse:
    """
    Search texts by category with pagination support.
    Returns first page and results_id for more pages.
    """
    return await corpus_service.search_by_category(category)

@router.post("/texts/search")
async def search_texts(
    data: TextSearch,
    corpus_service: CorpusService = Depends()
) -> SearchResponse:
    """
    Full text search with pagination and caching.
    Supports lemma search and category filtering.
    """
    return await corpus_service.search_texts(
        data.query,
        search_lemma=data.search_lemma,
        categories=data.categories
    )

@router.post("/texts/get-page")
async def get_results_page(
    params: PaginationParams,
    citation_service: CitationService = Depends()
) -> PaginatedResponse:
    """
    Get a specific page of search results from cache.
    """
    return await citation_service.get_paginated_results(
        params.results_id,
        params.page,
        params.page_size
    )
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

redis:
  url: "redis://localhost:6379"
  prefix: "atlomy"
  ttl: 3600
  chunk_size: 1000

## Caching Strategy

### Redis Structure
```
{prefix}:{results_id}:meta         - Search result metadata
{prefix}:{results_id}:chunk:{n}    - Result chunks
{prefix}:search:{query_hash}       - Search result cache
```

### Chunk Management
- Results split into configurable chunks
- Each chunk cached separately
- Metadata tracks total results and chunks
- Efficient page retrieval

### Cache Flow
1. Check cache for search results
2. Execute search if not cached
3. Store results in chunks
4. Return results_id and first page
5. Retrieve additional pages as needed

## Next Steps
1. Review the Database Schema
2. Understand the Query Patterns
3. Follow the Implementation Guide
4. Optimize Redis Configuration
5. Monitor Cache Performance
