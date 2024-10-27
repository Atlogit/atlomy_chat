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
    book_number TEXT,
    chapter_number TEXT,
    section_number TEXT,
    page_number INTEGER,
    metadata JSONB
);

CREATE TABLE text_lines (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES text_divisions,
    line_number INTEGER,
    content TEXT,
    spacy_tokens JSONB,  -- Full spaCy analysis
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
            
            # Create text divisions and lines
            for line in data['lines']:
                text_line = TextLine(
                    content=line['text'],
                    spacy_tokens=line['nlp_data']
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

### Phase 3: Service Layer Implementation

```python
# app/services/text_service.py
class TextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_category(self, category: str):
        query = """
        SELECT t.*, tl.*
        FROM texts t
        JOIN text_lines tl ON t.id = tl.text_id
        WHERE tl.spacy_tokens->'spans' @> $1
        """
        return await self.db.execute(query, {'label': category})

# app/services/analysis_service.py
class AnalysisService:
    def __init__(self, db: AsyncSession, bedrock_client):
        self.db = db
        self.llm = bedrock_client

    async def analyze_term(self, term: str, contexts: List[dict]):
        # Get analysis from AWS Bedrock
        analysis = await self.llm.analyze(term, contexts)
        
        # Store in database
        async with self.db.begin():
            lemma = Lemma(term=term)
            self.db.add(lemma)
            
            analysis_entry = LemmaAnalysis(
                lemma_id=lemma.id,
                analysis_data=analysis
            )
            self.db.add(analysis_entry)
```

### Phase 4: API Layer Updates

```python
# app/api/endpoints/texts.py
@router.get("/texts/search/{category}")
async def search_texts(
    category: str,
    db: AsyncSession = Depends(get_db),
    text_service: TextService = Depends()
):
    return await text_service.find_by_category(category)

# app/api/endpoints/analysis.py
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

### Phase 5: Frontend Integration

```javascript
// frontend/src/services/api.js
class TextAPI {
    async searchByCategory(category) {
        const response = await fetch(`/api/texts/search/${category}`);
        return response.json();
    }

    async analyzeTerm(term, contexts) {
        const response = await fetch('/api/analyze/term', {
            method: 'POST',
            body: JSON.stringify({ term, contexts })
        });
        return response.json();
    }
}
```

## 5. Testing Strategy

```python
# tests/test_text_service.py
async def test_find_by_category():
    async with AsyncTestClient(app) as client:
        response = await client.get("/texts/search/Body Part")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

# tests/test_analysis_service.py
async def test_term_analysis():
    async with AsyncTestClient(app) as client:
        response = await client.post("/analyze/term", 
            json={"term": "αἷμα", "contexts": []}
        )
        assert response.status_code == 200
```

## 6. Deployment Considerations

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=ancient_texts
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db/ancient_texts
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    depends_on:
      - db

  web:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - api
```
