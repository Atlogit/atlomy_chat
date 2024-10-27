# Common Query Patterns

## Text Search Queries

### Find Terms by Category
```sql
SELECT 
    t.title,
    td.book_number,
    td.chapter_number,
    tl.line_number,
    tl.content,
    tl.spacy_tokens->'spans' as spans
FROM text_lines tl
JOIN text_divisions td ON tl.division_id = td.id
JOIN texts t ON td.text_id = t.id
WHERE tl.spacy_tokens->'spans' @> '[{"label": "Body Part"}]';
```

### Parallel Text Retrieval
```sql
SELECT 
    tl.content as modern_text,
    tl.early_quote as early_text,
    td.book_number,
    td.early_chapter
FROM text_lines tl
JOIN text_divisions td ON tl.division_id = td.id
WHERE tl.word = $1;
```

### Citation Resolution
```sql
SELECT t.title, t.author
FROM texts t
WHERE t.reference_code = '[0057]';
```

## Lemma Operations

### Create New Lemma with Translations
```sql
INSERT INTO lemmas (
    lemma,
    source_language,
    translations,
    category_types
) VALUES (
    'αἷμα',
    'grc',
    '{"EN": "blood", "AR": "دم"}'::jsonb,
    ARRAY['Body Part']
);
```

### Update Lemma Analysis
```sql
UPDATE lemmas
SET descriptions = jsonb_set(
    descriptions,
    '{long,EN}',
    $1::jsonb
)
WHERE lemma = $2;
```

## Analysis Queries

### Gather Context for Analysis
```sql
WITH term_occurrences AS (
    SELECT 
        tl.id,
        tl.content,
        t.title,
        td.book_number,
        td.chapter_number
    FROM text_lines tl
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    WHERE tl.spacy_tokens->'tokens' @> '[{"lemma": $1}]'
)
SELECT *
FROM term_occurrences
ORDER BY book_number::int, chapter_number::int
LIMIT 10;
```

### Cross-Reference Search
```sql
SELECT 
    t1.content as source_text,
    t2.content as referenced_text
FROM text_lines t1
JOIN cross_references cr ON t1.id = cr.source_line_id
JOIN text_lines t2 ON cr.target_line_id = t2.id
WHERE t1.word = $1;
```

## Performance Optimization

### Indexes for Common Queries
```sql
-- Category search optimization
CREATE INDEX idx_category_search ON text_lines 
USING gin((spacy_tokens->'spans'));

-- Full text search
CREATE INDEX idx_text_search ON text_lines 
USING gin(to_tsvector('greek', content));

-- Reference lookup
CREATE INDEX idx_reference_lookup ON texts(reference_code);
```

### Materialized Views
```sql
CREATE MATERIALIZED VIEW common_terms AS
SELECT 
    l.lemma,
    l.translations,
    count(*) as occurrence_count
FROM lemmas l
JOIN word_occurrences wo ON l.id = wo.lemma_id
GROUP BY l.id, l.lemma, l.translations
HAVING count(*) > 10;
```

## SQLAlchemy Integration

### Query Examples
```python
# Category search
async def find_by_category(category: str):
    query = select(TextLine).join(TextDivision).join(Text).where(
        TextLine.spacy_tokens['spans'].contains([{'label': category}])
    )
    return await session.execute(query)

# Lemma creation
async def create_lemma(lemma_data: dict):
    lemma = Lemma(
        lemma=lemma_data['lemma'],
        translations=lemma_data['translations'],
        category_types=lemma_data['categories']
    )
    session.add(lemma)
    await session.commit()
    return lemma
```

## Next Steps
- Review [Migration Strategy](../migration/strategy.md)
- Implement [Toolkit](../implementation/toolkit_guide.md)
- Configure [Application](../implementation/application_guide.md)
