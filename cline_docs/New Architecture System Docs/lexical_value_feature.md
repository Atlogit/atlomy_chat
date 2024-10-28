# Lexical Value Creation Feature

## Overview
The lexical value creation tool analyzes ancient Greek terms using a combination of database citations and LLM-powered analysis. This feature maintains the functionality of the old system while integrating with the new architecture.

## Components

### 1. Database Schema
```sql
CREATE TABLE lexical_values (
    id UUID PRIMARY KEY,
    lemma VARCHAR NOT NULL UNIQUE,
    translation VARCHAR,
    short_description TEXT,
    long_description TEXT,
    related_terms VARCHAR[],
    citations_used JSONB,
    references JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Enhanced text_divisions with author and work names
ALTER TABLE text_divisions
ADD COLUMN author_name VARCHAR,
ADD COLUMN work_name VARCHAR;
```

### 2. Citation Handling
- **Enhanced Citation Format**: Citations now include full author and work names instead of just ID numbers
- **Example**: "Hippocrates Med. et Corpus Hippocraticum, Prognosticon (Chapter 2, Lines 10-15)" instead of "[0627] [003] (Chapter 2, Lines 10-15)"
- **Source**: Names are derived from TLG indexes for accuracy and consistency
- **Storage**: Author and work names are stored directly in the text_divisions table for efficient querying

### 3. Service Layer
- **LexicalService**: Manages lexical value operations
  - Enhanced citation retrieval with proper author/work names
  - Redis caching
  - CRUD operations
  - Task status management
  - Data validation
  - Required fields validation

- **LLMService**: Handles AI analysis
  - Specialized template for lexical analysis
  - Citation formatting with proper names
  - Response validation
  - Error handling

### 4. API Endpoints
```python
POST /lexical/create
{
    "lemma": "φλέψ",
    "search_lemma": true
}

GET /lexical/status/{task_id}
GET /lexical/get/{lemma}
GET /lexical/list
PUT /lexical/update/{lemma}
DELETE /lexical/delete/{lemma}
```

## Workflow

1. **Citation Gathering**
   ```sql
   -- Example citation query with enhanced naming
   WITH matched_sentences AS (
       SELECT DISTINCT ON (s.id)
           s.content as sentence_text,
           td.author_name,
           td.work_name,
           td.volume,
           td.chapter,
           array_agg(tl.line_number) as line_numbers
       FROM sentences s
       JOIN text_lines tl ON s.text_line_id = tl.id
       JOIN text_divisions td ON tl.division_id = td.id
       WHERE CAST(s.spacy_tokens AS TEXT) ILIKE '%"lemma":"desired_lemma"%'
   )
   SELECT * FROM matched_sentences;
   ```

2. **LLM Analysis**
   ```python
   # Required fields in LLM response
   {
       "lemma": word,
       "translation": "...",
       "short_description": "...",
       "long_description": "...",
       "related_terms": [...],
       "citations_used": [...]  # Now includes properly formatted citations
   }
   ```

3. **Data Validation**
   ```python
   # Validate required fields
   required_fields = [
       'lemma',
       'translation',
       'short_description',
       'long_description',
       'related_terms',
       'citations_used'
   ]
   ```

4. **Storage & Caching**
   ```python
   # Redis caching with enhanced citation format
   cache_key = f"lexical_value:{lemma}"
   await redis_client.set(cache_key, json.dumps(data), ttl=3600)
   ```

## Example Usage

```python
# Create a lexical value
lexical_service = LexicalService(db)
result = await lexical_service.create_lexical_entry(
    lemma="φλέψ",
    search_lemma=True
)

# Result structure with enhanced citations
{
    "success": True,
    "message": "Lexical value created successfully",
    "entry": {
        "lemma": "φλέψ",
        "translation": "vein, blood vessel",
        "short_description": "...",
        "long_description": "...",
        "related_terms": ["αἷμα", "ἀρτηρία"],
        "citations_used": [
            {
                "sentence": "...",
                "citation": "Hippocrates Med., Prognosticon (Chapter 2, Lines 10-15)",
                "context": {...},
                "location": {...}
            }
        ]
    },
    "action": "create"
}
```

## Testing

The feature includes comprehensive tests:
- Creation workflow with enhanced citations
- Citation retrieval and formatting
- LLM integration
- Error handling
  - Missing required fields
  - Invalid LLM responses
  - Database errors
- Cache management
- Existing entry handling

Run tests with:
```bash
pytest tests/test_lexical_value_creation.py -v
```

## Performance Considerations

1. **Database**
   - Indexed author_name and work_name fields
   - JSONB for flexible storage
   - Connection pooling

2. **Caching**
   - Redis for frequent lookups
   - Configurable TTL
   - Cache invalidation on updates

3. **Background Processing**
   - Async task handling
   - Status tracking
   - Error recovery

## Error Handling

1. **API Level**
   - Input validation
   - Task status tracking
   - Detailed error responses

2. **Service Level**
   - Database error handling
   - LLM response validation
   - Required fields validation
   - Cache error recovery

3. **Data Level**
   - Citation validation
   - Response format checking
   - Required field validation
   - JSON structure validation

## Monitoring

Key metrics to monitor:
- Creation task success rate
- LLM response times
- Cache hit/miss ratio
- Database query performance
- Error rates by type
- Validation failure rates

## Future Improvements

1. **Performance**
   - Batch citation processing
   - Improved caching strategies
   - Query optimization

2. **Features**
   - Bulk creation support
   - Enhanced citation context
   - Version history
   - Enhanced validation rules

3. **Integration**
   - Additional LLM providers
   - Enhanced error recovery
   - Automated testing improvements

## Troubleshooting

1. **Citation Issues**
   - Check author_name and work_name in text_divisions
   - Verify TLG index mappings
   - Review citation formatting

2. **Cache Issues**
   - Check Redis connection
   - Clear cache if needed:
     ```python
     await redis_client.flushdb()
     ```

3. **LLM Response Issues**
   - Check AWS credentials
   - Verify prompt template
   - Monitor token limits
   - Validate response structure

4. **Validation Errors**
   - Check required fields are present
   - Verify JSON structure
   - Review LLM response format
