# Database Setup and Processing Guide

## Initial Setup

### 1. Database Creation
```bash
# Create PostgreSQL database
createdb amta_greek

# Initialize Alembic
alembic init migrations

# Run migrations
alembic upgrade head
```

### 2. Environment Configuration
```bash
# Required environment variables
POSTGRES_DB=amta_greek
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Optional Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Data Processing Pipeline

### 1. Text Ingestion

#### A. Author and Text Setup
```python
# Create author entry
author = Author(
    name="Hippocrates",
    reference_code="[0086]",
    language_code="grc"
)

# Create text entry
text = Text(
    author=author,
    reference_code="[055]",
    title="De Morbis"
)
```

#### B. Text Division Processing
```python
# Process text divisions
division = TextDivision(
    text=text,
    author_id_field="[0086]",
    work_number_field="[055]",
    author_name="Hippocrates",
    work_name="De Morbis",
    chapter="1",
    section="2"
)
```

#### C. Line Processing with NLP
```python
# Process individual lines with spaCy
nlp = spacy.load("grc")
doc = nlp(line_text)

text_line = TextLine(
    division=division,
    line_number=1,
    content=line_text,
    categories=extract_categories(doc),
    spacy_tokens={
        "tokens": [token_to_dict(t) for t in doc],
        "spans": [span_to_dict(s) for s in doc.ents]
    }
)
```

### 2. Sentence Processing

#### A. Sentence Extraction
```python
# Extract sentences from lines
def process_sentences(text_lines):
    for line in text_lines:
        doc = nlp(line.content)
        for sent in doc.sents:
            sentence = Sentence(
                content=sent.text,
                source_line_ids=[line.id],
                start_position=sent.start_char,
                end_position=sent.end_char,
                spacy_data=sentence_to_dict(sent),
                categories=extract_categories(sent)
            )
            # Create association
            sentence.text_lines.append(line)
```

### 3. Lexical Analysis

#### A. Lemma Processing
```python
# Create lemma entries
lemma = Lemma(
    lemma="αἷμα",
    language_code="grc",
    categories=["Body_Part", "Medical_Term"],
    translations={
        "EN": "blood",
        "AR": "دم"
    }
)
```

#### B. LLM Analysis Generation
```python
# Generate analysis using AWS Bedrock
analysis = LemmaAnalysis(
    lemma=lemma,
    analysis_text=llm_response.text,
    analysis_data=llm_response.structured_data,
    citations=extract_citations(llm_response),
    created_by="Claude-3"
)
```

#### C. Lexical Value Creation
```python
# Create lexical value with context
lexical_value = LexicalValue(
    lemma="αἷμα",
    translation="blood",
    short_description="Vital bodily fluid",
    sentence_contexts={
        str(sentence.id): {
            "text": sentence.content,
            "prev": get_prev_sentence(sentence),
            "next": get_next_sentence(sentence)
        }
    }
)
```

## Maintenance Tasks

### 1. Database Optimization
```sql
-- Analyze tables for query optimization
ANALYZE authors, texts, text_divisions, text_lines;

-- Update statistics
VACUUM ANALYZE;

-- Reindex when needed
REINDEX TABLE text_lines;
```

### 2. Data Validation
```python
def validate_data_integrity():
    # Check citation links
    validate_citations()
    
    # Verify sentence boundaries
    validate_sentence_boundaries()
    
    # Check NLP data consistency
    validate_nlp_data()
```

### 3. Backup Strategy
```bash
# Daily backup
pg_dump ancient_texts_db > backup_$(date +%Y%m%d).sql

# Backup specific schemas
pg_dump -n public ancient_texts_db > schema_backup.sql
```

## Performance Monitoring

### 1. Query Performance
```sql
-- Monitor slow queries
SELECT * FROM pg_stat_activity 
WHERE state = 'active' 
  AND now() - query_start > interval '5 seconds';

-- Check index usage
SELECT * FROM pg_stat_user_indexes;
```

### 2. Storage Monitoring
```sql
-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Monitor JSONB field sizes
SELECT avg(length(spacy_tokens::text))
FROM text_lines;
```

### 3. Cache Management
```python
# Redis cache configuration
cache_config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_DEFAULT_TIMEOUT': 300
}

# Cache common queries
@cache.memoize(timeout=300)
def get_text_by_citation(author_id, work_id):
    return TextDivision.query.filter_by(
        author_id_field=author_id,
        work_number_field=work_id
    ).first()
```

## Error Handling

### 1. Database Errors
```python
def handle_db_error(error):
    if isinstance(error, IntegrityError):
        # Handle duplicate keys, foreign key violations
        log_integrity_error(error)
    elif isinstance(error, OperationalError):
        # Handle connection issues
        reconnect_to_db()
```

### 2. Data Processing Errors
```python
def handle_processing_error(error):
    if isinstance(error, NLPError):
        # Handle spaCy processing errors
        fallback_to_basic_processing()
    elif isinstance(error, LLMError):
        # Handle AWS Bedrock errors
        retry_with_backoff()
```

## Next Steps

1. **Monitoring Setup**:
   - Implement query logging
   - Set up performance monitoring
   - Configure error alerting

2. **Optimization**:
   - Review and optimize indexes
   - Implement caching strategy
   - Configure connection pooling

3. **Maintenance**:
   - Schedule regular backups
   - Plan vacuum and analyze operations
   - Monitor storage usage
