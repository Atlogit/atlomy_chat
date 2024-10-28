# Ancient Medical Texts Analysis: Architecture Migration Guide

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
│   └── JSONB support for spaCy data
├── SQLAlchemy 2.0
│   └── Async support
└── Alembic (migrations)

API Layer:
├── asyncpg
└── FastAPI dependency injection

Caching (optional):
└── Redis
```

## 3. Database Schema Design

```sql
-- Core Text Storage
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    language_code VARCHAR(5)
);

CREATE TABLE texts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER REFERENCES authors,
    reference_code VARCHAR(20),  -- [0057] format
    title TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE text_divisions (
    id SERIAL PRIMARY KEY,
    text_id INTEGER REFERENCES texts,
    -- Citation components
    author_id_field VARCHAR(20) NOT NULL,    -- e.g., [0086]
    work_number_field VARCHAR(20) NOT NULL,   -- e.g., [055]
    epithet_field VARCHAR(100),              -- e.g., [Divis]
    fragment_field VARCHAR(100),             -- Optional fragment reference
    -- Structural components
    volume VARCHAR(50),                      -- Volume reference
    chapter VARCHAR(50),                     -- Chapter reference
    line VARCHAR(50),                        -- Line reference
    section VARCHAR(50),                     -- Section reference (e.g., 847a)
    -- Title components
    is_title BOOLEAN DEFAULT FALSE,
    title_number VARCHAR(50),                -- Title reference number
    title_text TEXT,                         -- Title content
    -- Additional metadata
    division_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE text_lines (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES text_divisions,
    line_number INTEGER,
    content TEXT,
    categories TEXT[],                       -- Array of category tags
    spacy_tokens JSONB,                      -- Full spaCy analysis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Storage
CREATE TABLE lemmas (
    id SERIAL PRIMARY KEY,
    lemma TEXT NOT NULL,
    language_code VARCHAR(5),
    category TEXT[],
    translations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lemma_analyses (
    id SERIAL PRIMARY KEY,
    lemma_id INTEGER REFERENCES lemmas,
    analysis_text TEXT,
    analysis_data JSONB,
    citations JSONB,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. Migration Steps

### Phase 1: Setup & Infrastructure

1. Database Setup:
```bash
# Install PostgreSQL
sudo apt-get install postgresql-14

# Create database
createdb ancient_texts_db

# Initialize Alembic
alembic init migrations
```

2. Project Structure Update:
```
ancient_texts/
├── alembic/
│   └── versions/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   └── database.py
│   └── services/
│       ├── text_service.py
│       └── analysis_service.py
├── migrations/
└── docker-compose.yml
```

### Phase 2: Data Migration

1. Create Migration Scripts:
```python
# app/scripts/migrate_data.py
async def migrate_texts():
    """Migrate existing JSON data to PostgreSQL"""
    async with AsyncSessionLocal() as session:
        # Read existing JSON files
        for json_file in json_files:
            data = load_json(json_file)
            
            # Create text entry
            text = Text(
                reference_code=data['reference'],
                title=data['title']
            )
            session.add(text)
            
            # Create text divisions with citation and structural components
            for division in data['divisions']:
                text_division = TextDivision(
                    text_id=text.id,
                    author_id_field=division['author_id'],
                    work_number_field=division['work_number'],
                    epithet_field=division.get('epithet'),
                    fragment_field=division.get('fragment'),
                    volume=division.get('volume'),
                    chapter=division.get('chapter'),
                    line=division.get('line'),
                    section=division.get('section')
                )
                session.add(text_division)
                
                # Create text lines
                for line in division['lines']:
                    text_line = TextLine(
                        division_id=text_division.id,
                        line_number=line['number'],
                        content=line['text'],
                        categories=line.get('categories', []),
                        spacy_tokens=line.get('nlp_data')
                    )
                    session.add(text_line)
        
        await session.commit()
```

2. Run Migrations:
```bash
# Create initial tables
alembic upgrade head

# Run data migration
python -m app.scripts.migrate_data
```

[Rest of the document remains unchanged...]
