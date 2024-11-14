# Citation System Documentation

## Overview

The citation system has been updated to work directly with sentences as the primary unit of citation. This change improves efficiency by eliminating unnecessary LLM processing for simple citation lookups while maintaining rich context and relationships. The system includes caching, JSON storage versioning, and robust error handling.

## Key Components

### 1. Database Structure

#### Sentences Table
```sql
CREATE TABLE sentences (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source_line_ids INTEGER[] NOT NULL,
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    spacy_data JSONB,
    categories TEXT[]
);
```

#### Sentence-TextLine Association
```sql
CREATE TABLE sentence_text_lines (
    sentence_id INTEGER REFERENCES sentences ON DELETE CASCADE,
    text_line_id INTEGER REFERENCES text_lines ON DELETE CASCADE,
    position_start INTEGER NOT NULL,
    position_end INTEGER NOT NULL,
    PRIMARY KEY (sentence_id, text_line_id)
);
```

#### LexicalValue Relationship
- many-to-many relationship with sentences
- Stores sentence contexts and citation metadata
- Maintains backwards compatibility with existing citation format

### 2. Citation Queries

The system supports multiple specialized query types for different citation lookup scenarios:

#### Base Citation Query Structure
All citation queries share a common base structure that:
- Joins sentences with text lines and divisions
- Provides sentence context (previous and next sentences)
- Includes author and work information
- Maintains consistent ordering
- Groups results to avoid duplicates

#### Direct Sentence Query
- Optimized for retrieving citations without LLM processing
- Used for simple lemma lookups
- Maintains full sentence context and relationships
- Uses lateral join for efficient token processing

```sql
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.volume,
        td.chapter,
        td.section,
        LAG(s.content) OVER w as prev_sentence,
        LEAD(s.content) OVER w as next_sentence
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id,
    LATERAL jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token
    WHERE token->>'lemma' = :pattern
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number
```

#### Specialized Query Types

1. **Lemma Citation Query**
   - Searches for lemmas in spaCy token data
   - Uses JSON field traversal for token analysis
   - Condition: `EXISTS (SELECT 1 FROM jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token WHERE token->>'lemma' = :pattern)`

2. **Text Citation Query**
   - Full-text search in sentence content
   - Uses ILIKE for case-insensitive matching
   - Condition: `s.content ILIKE :pattern`

3. **Category Citation Query**
   - Searches sentences by their categories
   - Uses array containment operator
   - Condition: `s.categories @> ARRAY[:category]::VARCHAR[]`

4. **Citation Search Query**
   - Looks up citations by author and work identifiers
   - Direct match on division fields
   - Condition: `td.author_id_field = :author_id AND td.work_number_field = :work_number`

### 3. Citation Pattern Matching

The system supports flexible citation pattern matching through a configuration-driven approach. Patterns are defined in `citation_config.json` and include:

#### Standard Reference Patterns
```json
{
  "pattern": "(\\d+)\\.(\\d+)\\.(\\d+)",
  "groups": ["volume", "chapter", "line"],
  "format": "Volume {volume}, Page {chapter}, Line {line}"
}
```

#### Title Reference Pattern
```json
{
  "pattern": "^\\.t\\.(\\d+)",
  "groups": ["title_number"],
  "format": "Title {title_number}"
}
```

#### Complex Reference Pattern
```json
{
  "pattern": "(\\d+)\\.(\\d+)\\.(\\d+)\\.(\\d+)",
  "groups": ["volume", "chapter", "subdivision", "line"],
  "format": "Book {volume}, Chapter {chapter}, Section {subdivision}, Line {line}"
}
```

These patterns support:
- Standard volume.chapter.line references
- Title-specific references
- Complex hierarchical references
- Author and work identification
- Mixed alphanumeric references

### 4. Caching System

#### Redis Cache Implementation
- Page-based storage for efficient pagination
- Direct page access without full dataset deserialization
- TTL-based caching (configurable)
- Automatic cache invalidation on updates

#### Redis Storage Structure
```
{prefix}:{results_id}:meta         - Metadata (total results, total pages, page size)
{prefix}:{results_id}:page:{n}     - Individual page data
{prefix}:search:{query_hash}       - Search result cache
```

#### Page Management
- Results split into pages (default 10 items per page)
- Each page stored separately with same TTL
- Metadata tracks total pages and page size
- Direct access to specific pages without loading entire dataset

#### Pagination Flow
1. Client makes search request
2. Server executes query and formats citations
3. Citations stored in Redis by page
4. Results ID returned with first page
5. Client requests additional pages using results_id
6. Server retrieves specific page directly

#### Performance Optimization
- Direct page access without loading full dataset
- Reduced memory usage per request
- Faster response times for pagination
- Efficient cache utilization

#### Cache Keys
- Results ID: UUID for each search
- Search Cache: Hash of search parameters
- Page Keys: Sequential page numbers
- Metadata: Stores total results and pagination info

### 5. JSON Storage

#### Version Control
- Maintains multiple versions of lexical values
- Supports rollback capabilities
- Version-specific retrieval
- Automatic JSON storage on updates

## Citation Flow

1. **Initial Request**
   - Check Redis cache for existing entry
   - If not in cache, check JSON storage
   - Finally, query database if needed

2. **Citation Lookup**
   - Select appropriate query type based on search criteria
   - Execute optimized query for specific use case
   - Retrieve full sentence context and metadata
   - No LLM processing needed for basic lookups

3. **Context Handling**
   - Previous and next sentences maintained
   - Position information preserved
   - Full NLP analysis available
   - Sentence contexts stored with lexical values

4. **Citation Formatting**
   - Pattern matching based on configuration
   - Standard citation format maintained
   - Author and work information included
   - Location data (volume, chapter, section) preserved
   - Support for abbreviated citations

5. **Error Handling**
   - Comprehensive logging at all steps
   - Graceful fallback mechanisms
   - Cache invalidation on errors
   - Transaction management for database operations

## Benefits

1. **Improved Efficiency**
   - Multi-level caching system
   - Eliminated unnecessary LLM processing
   - Optimized database queries
   - Direct sentence-based lookups

2. **Rich Context**
   - Complete sentence preservation
   - Position tracking in source texts
   - Full NLP analysis data
   - Version control for lexical values

3. **Maintainable Structure**
   - Clear separation of concerns
   - Well-defined relationships
   - Backwards compatible
   - Robust error handling

## Usage Examples

### Getting Citations for a Lemma
```python
# Direct sentence query without LLM
citations = await lexical_service._get_citations(lemma, search_lemma=True)
```

### Linking Citations to Lexical Values
```python
# Add direct sentence link
lexical_value.sentence_id = sentence_id
lexical_value.sentence_contexts[sentence_id] = context
```

### Retrieving Linked Citations
```python
# Get citations with full context
citations = await lexical_service.get_linked_citations(lemma)
```

### Managing Versions
```python
# Get available versions
versions = await lexical_service.get_json_versions(lemma)

# Get specific version
value = await lexical_service.get_lexical_value(lemma, version="v1")
```

## Future Considerations

1. **Performance Optimization**
   - Cache warming strategies
   - Index optimization for sentence queries
   - Batch processing for large datasets
   - Cache eviction policies

2. **Feature Extensions**
   - Enhanced context analysis
   - Advanced citation formatting options
   - Additional metadata support
   - Improved version control

3. **Integration Points**
   - API endpoint optimization
   - Frontend display improvements
   - Export format extensions
   - Bulk operation support
