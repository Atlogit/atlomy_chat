# Ancient Medical Texts Analysis: Architecture Overview

## 1. System Architecture Overview

### Current System
```
[Frontend (HTML/Tailwind/JS)] 
         ↓
[FastAPI Backend]
         ↓
[AWS Bedrock (Claude-3)]
         ↓
[File-based/JSON Storage]
```

### New System Architecture
```
[Frontend (HTML/Tailwind/JS)] 
         ↓
[FastAPI Backend]
         ↓
    [Services Layer]
         ↓
[Database Layer (PostgreSQL)]
         ↕
[AWS Bedrock (Claude-3)]
         ↕
[Redis Cache (Optional)]
```

## 2. Tech Stack Evolution

### Retained Components
```
Frontend:
├── HTML5
├── Tailwind CSS (v3.4.1)
├── DaisyUI (v4.7.2)
└── JavaScript (ES6+)

Backend:
├── FastAPI
├── Python 3.9+
└── AWS Bedrock (Claude-3-sonnet)
```

### New Components
```
Database:
├── PostgreSQL 14+
│   ├── JSONB support for spaCy data
│   ├── Array types for categories
│   └── UUID support for analysis IDs
├── SQLAlchemy 2.0
│   ├── Async support (AsyncAttrs)
│   ├── Declarative models
│   └── Relationship management
└── Alembic (migrations)

API Layer:
├── asyncpg
├── FastAPI dependency injection
└── Async session management

Caching:
└── Redis (optional)
    ├── Query results
    └── Frequent lookups
```

## 3. Database Schema Design

### Core Text Storage

```sql
-- Authors table for storing author information
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    reference_code VARCHAR(20) NOT NULL UNIQUE,
    normalized_name TEXT,
    language_code VARCHAR(5),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Texts table for storing main text documents
CREATE TABLE texts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER REFERENCES authors ON DELETE CASCADE,
    reference_code VARCHAR(20),
    title TEXT NOT NULL,
    text_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Text divisions for structural and citation components
CREATE TABLE text_divisions (
    id SERIAL PRIMARY KEY,
    text_id INTEGER REFERENCES texts ON DELETE CASCADE,
    -- Citation components
    author_id_field VARCHAR(20) NOT NULL,
    work_number_field VARCHAR(20) NOT NULL,
    epithet_field VARCHAR(100),
    fragment_field VARCHAR(100),
    -- Author and work names
    author_name TEXT,
    work_name TEXT,
    -- Structural components
    volume VARCHAR(50),
    chapter VARCHAR(50),
    line VARCHAR(50),
    section VARCHAR(50),
    -- Title components
    is_title BOOLEAN DEFAULT FALSE,
    title_number VARCHAR(50),
    title_text TEXT,
    -- Additional metadata
    division_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Text lines with NLP analysis
CREATE TABLE text_lines (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES text_divisions ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    categories TEXT[],
    spacy_tokens JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### Analysis Storage

```sql
-- Sentences parsed from text lines
CREATE TABLE sentences (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source_line_ids INTEGER[] NOT NULL,
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    spacy_data JSONB,
    categories TEXT[],
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Association table for sentences and text lines
CREATE TABLE sentence_text_lines (
    sentence_id INTEGER REFERENCES sentences ON DELETE CASCADE,
    text_line_id INTEGER REFERENCES text_lines ON DELETE CASCADE,
    position_start INTEGER NOT NULL,
    position_end INTEGER NOT NULL,
    PRIMARY KEY (sentence_id, text_line_id)
);

-- Lemmas with translations and categories
CREATE TABLE lemmas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma TEXT NOT NULL,
    language_code VARCHAR(5),
    categories TEXT[],
    translations JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- LLM-generated analyses for lemmas
CREATE TABLE lemma_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma_id UUID REFERENCES lemmas ON DELETE CASCADE,
    analysis_text TEXT NOT NULL,
    analysis_data JSONB,
    citations JSONB,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Lexical values with sentence contexts
CREATE TABLE lexical_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma TEXT NOT NULL UNIQUE,
    translation TEXT,
    short_description TEXT,
    long_description TEXT,
    related_terms TEXT[],
    citations_used JSONB,
    references JSONB,
    sentence_contexts JSONB,
    sentence_id INTEGER REFERENCES sentences,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## 4. Key Features

### Async Support
- All models inherit from AsyncAttrs for async operations
- Async session management in FastAPI endpoints
- Connection pooling with asyncpg

### Relationship Management
```
Author ─┬─> Text ─┬─> TextDivision ─> TextLine ─┬─> Sentence
        │         │                             │
        │         │                             └─> spaCy Analysis
        │         │
        │         └─> Metadata (JSONB)
        │
Lemma <──┘
  │
  ├─> LemmaAnalysis
  └─> LexicalValue ─> SentenceContext
```

### Data Types
- JSONB for flexible metadata and NLP data
- Arrays for categories and related terms
- UUIDs for analysis identifiers
- Timestamps for all models

### Performance Features
- Indexes on frequently queried fields
- Cascade deletes for referential integrity
- Optional Redis caching layer

## 5. Migration Strategy

### Phase 1: Infrastructure
1. Set up PostgreSQL with required extensions
2. Initialize Alembic for migrations
3. Configure async database connection

### Phase 2: Data Migration
1. Create tables using Alembic migrations
2. Migrate existing JSON data
3. Validate data integrity

### Phase 3: API Updates
1. Update FastAPI endpoints for async
2. Implement service layer
3. Add caching where needed

## 6. Next Steps

1. **Schema Implementation**:
   - Run migrations
   - Validate relationships
   - Test constraints

2. **Data Processing**:
   - Implement NLP pipeline
   - Set up LLM integration
   - Configure caching

3. **API Development**:
   - Update endpoints
   - Add async support
   - Implement services

4. **Documentation**:
   - API documentation
   - Query patterns
   - Performance guidelines
