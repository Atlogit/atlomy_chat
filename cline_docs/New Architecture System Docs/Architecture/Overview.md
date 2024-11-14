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
   - Efficient citation handling with Redis caching

## System Interaction Diagram

```
[Text Files] → [Text Processing Toolkit] → [Database] ← [Analysis Application] ← [Users]
                                            ↑ ↓              ↕
                                      [NLP Processing]    [Redis Cache]
                                            ↓               ↕
                                     [Elasticsearch]   [AWS Bedrock]
```

## Key Components
- PostgreSQL Database (shared resource)
- Redis Cache (pagination and search results)
- FastAPI Backend
- AWS Bedrock Integration
- spaCy NLP Pipeline
- Advanced Sentence Processing System
- Citation Management System

## Technology Stack
- Python 3.9+
- FastAPI
- PostgreSQL 14+
- Redis 6+
- SQLAlchemy 2.0
- spaCy
- AWS Bedrock
- Alembic

## Caching Architecture
- Redis-based chunked storage
- Metadata-driven pagination
- Search result caching
- Configurable TTL and chunk sizes

## Citation System
- Efficient citation formatting
- Context preservation
- Paginated result retrieval
- Redis-based caching strategy
- Chunk-based large result handling

## Next Steps
- Review the [Toolkit Architecture](toolkit.md)
- Review the [Application Architecture](application.md)
- Understand the [Database Schema](../database/schema.md)
- Study the [Sentence Processing Flow](../sentence_processing_flow.md)
- Review the [Citation System](../citation_system.md)


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
    ├── api/                   # FastAPI routes
    ├── services/             # Business logic
    │   ├── citation_service.py  # Citation handling
    │   └── search_service.py   # Search operations
    └── models/               # Data models
        └── citations.py      # Citation models
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
   - Citation management
   - Redis-based caching
