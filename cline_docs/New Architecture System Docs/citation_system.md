# Citation System Documentation

## Overview

The citation system has been updated to work directly with sentences as the primary unit of citation. This change improves efficiency by eliminating unnecessary LLM processing for simple citation lookups while maintaining rich context and relationships.

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
    sentence_id INTEGER REFERENCES sentences,
    text_line_id INTEGER REFERENCES text_lines,
    position_start INTEGER NOT NULL,
    position_end INTEGER NOT NULL,
    PRIMARY KEY (sentence_id, text_line_id)
);
```

### 2. Citation Queries

#### Direct Sentence Query
- Optimized for retrieving citations without LLM processing
- Used for simple lemma lookups
- Maintains full sentence context and relationships

```sql
SELECT 
    s.id as sentence_id,
    s.content as sentence_text,
    s.spacy_data as sentence_tokens,
    tl.line_number,
    td.author_name,
    td.work_name,
    td.volume,
    td.chapter,
    td.section,
    LAG(s.content) OVER w as prev_sentence,
    LEAD(s.content) OVER w as next_sentence
FROM sentences s
JOIN sentence_text_lines stl ON s.id = stl.sentence_id
JOIN text_lines tl ON stl.text_line_id = tl.id
JOIN text_divisions td ON tl.division_id = td.id
WHERE CAST(s.spacy_data AS TEXT) ILIKE :pattern
WINDOW w AS (PARTITION BY td.id ORDER BY tl.line_number)
ORDER BY td.id, tl.line_number;
```

### 3. Model Relationships

#### LexicalValue
- Direct relationship with sentences
- Stores sentence contexts and citation metadata
- Maintains backwards compatibility with existing citation format

#### Sentence
- Many-to-many relationship with text lines
- Stores complete sentence content and NLP analysis
- Tracks position information in source lines

## Citation Flow

1. **Citation Lookup**
   - Direct query to sentences table for lemma matches
   - Retrieves full sentence context and metadata
   - No LLM processing needed for basic lookups

2. **Context Handling**
   - Previous and next sentences maintained
   - Position information preserved
   - Full NLP analysis available

3. **Citation Formatting**
   - Standard citation format maintained
   - Author and work information included
   - Location data (volume, chapter, section) preserved

## Benefits

1. **Improved Efficiency**
   - Eliminated unnecessary LLM processing
   - Optimized database queries
   - Direct sentence-based lookups

2. **Rich Context**
   - Complete sentence preservation
   - Position tracking in source texts
   - Full NLP analysis data

3. **Maintainable Structure**
   - Clear separation of concerns
   - Well-defined relationships
   - Backwards compatible

## Usage Examples

### Getting Citations for a Lemma
```python
# Direct sentence query without LLM
citations = await lexical_service._get_citations(lemma, search_lemma=True)
```

### Linking Citations to Lexical Values
```python
# Add direct sentence link
lexical_value.add_citation_link(sentence_id, context)
```

### Retrieving Linked Citations
```python
# Get citations with full context
citations = lexical_value.get_linked_citations()
```

## Future Considerations

1. **Performance Optimization**
   - Index optimization for sentence queries
   - Caching strategies for frequent lookups
   - Batch processing for large datasets

2. **Feature Extensions**
   - Enhanced context analysis
   - Advanced citation formatting options
   - Additional metadata support

3. **Integration Points**
   - API endpoint optimization
   - Frontend display improvements
   - Export format extensions
