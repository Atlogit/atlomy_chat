# Lexical Value Creation Context

## Current Status

### Completed Features
1. Enhanced Citation Names
   - Author and work names added to database
   - TLG index integration
   - Proper citation formatting
   - Migration and data update completed

### In Progress Features
1. Sentence-Based Citations
   - Need to modify citation retrieval
   - Focus on complete sentences containing lemmas
   - Enhance context with full sentence text

2. Direct Citation Linking
   - Plan to create relationships between lexical values and text lines
   - Need to implement association table
   - Will improve citation tracking and querying

3. JSON Storage
   - Need to implement file-based storage
   - Will support versioning and backups
   - Requires proper organization structure

## Technical Context

### Database Structure
```sql
-- Existing tables
CREATE TABLE text_divisions (
    id SERIAL PRIMARY KEY,
    author_name VARCHAR,  -- Recently added
    work_name VARCHAR,    -- Recently added
    ...
);

-- Needed tables/modifications
CREATE TABLE lexical_value_citations (
    lexical_value_id UUID REFERENCES lexical_values(id),
    text_line_id INTEGER REFERENCES text_lines(id),
    context_type VARCHAR,
    PRIMARY KEY (lexical_value_id, text_line_id)
);
```

### Citation Flow
1. Current:
   - Query by lemma/word
   - Get text lines
   - Format with author/work names

2. Needed:
   - Query by lemma/word
   - Get complete sentences
   - Link to text lines
   - Store in JSON format

### Storage Structure
```
lexical_values/
  ├── by_lemma/
  │   ├── α/
  │   │   ├── ἀρτηρία.json
  │   │   └── ...
  │   └── ...
  ├── by_date/
  │   ├── 2024/
  │   │   ├── 03/
  │   │   │   ├── 21/
  │   │   │   │   └── ...
  │   │   └── ...
  └── versions/
      ├── ἀρτηρία/
      │   ├── v1.json
      │   └── v2.json
      └── ...
```

## Implementation Priorities

1. Sentence-Based Citations
   - Critical for proper context
   - Needed for LLM analysis
   - Improves citation quality

2. Citation Linking
   - Enables better tracking
   - Improves data relationships
   - Supports future features

3. JSON Storage
   - Provides data portability
   - Enables version control
   - Supports backups

## Considerations

### Performance
- Sentence queries may be slower
- Need proper indexing
- Consider caching strategies

### Data Integrity
- Maintain relationships
- Handle updates properly
- Ensure data consistency

### Scalability
- Plan for large datasets
- Consider batch processing
- Optimize storage structure

## Next Actions
1. Implement sentence-based citation retrieval
2. Create citation linking system
3. Set up JSON storage structure
4. Update documentation as we progress
