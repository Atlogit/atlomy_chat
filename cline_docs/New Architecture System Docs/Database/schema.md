# Database Schema Design

## Core Tables

### Authors
```sql
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    reference_code VARCHAR(20) NOT NULL UNIQUE,
    normalized_name TEXT,
    language_code VARCHAR(5)
);

CREATE INDEX idx_authors_reference_code ON authors(reference_code);
```

### Texts
```sql
CREATE TABLE texts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER REFERENCES authors,
    reference_code VARCHAR(20),
    title TEXT NOT NULL,
    text_metadata JSONB
);

CREATE INDEX idx_texts_reference_code ON texts(reference_code);
```

### Text Divisions
```sql
CREATE TABLE text_divisions (
    id SERIAL PRIMARY KEY,
    text_id INTEGER REFERENCES texts ON DELETE CASCADE,
    -- Citation components
    author_id_field VARCHAR(20) NOT NULL,    -- e.g., [0086]
    work_number_field VARCHAR(20) NOT NULL,   -- e.g., [055]
    epithet_field VARCHAR(100),              -- e.g., [Divis]
    fragment_field VARCHAR(100),             -- Optional fragment reference
    -- Author and work names
    author_name TEXT,
    work_name TEXT,
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
    division_metadata JSONB
);
```

### Text Lines
```sql
CREATE TABLE text_lines (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES text_divisions ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    categories TEXT[],                       -- Array of category tags
    spacy_tokens JSONB                       -- Full spaCy analysis
);

CREATE INDEX idx_text_lines_categories ON text_lines USING GIN(categories);
CREATE INDEX idx_text_lines_spacy_tokens ON text_lines USING GIN(spacy_tokens);
```

## Analysis Tables

### Sentences
```sql
CREATE TABLE sentences (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source_line_ids INTEGER[] NOT NULL,      -- IDs of TextLine objects
    start_position INTEGER NOT NULL,         -- Start position in first line
    end_position INTEGER NOT NULL,           -- End position in last line
    spacy_data JSONB,                       -- Complete spaCy analysis
    categories TEXT[]                        -- Categories from analysis
);

CREATE INDEX idx_sentences_categories ON sentences USING GIN(categories);
CREATE INDEX idx_sentences_source_lines ON sentences USING GIN(source_line_ids);

```

### Sentence-TextLine Association
```sql
CREATE TABLE sentence_text_lines (
    sentence_id INTEGER REFERENCES sentences ON DELETE CASCADE,
    text_line_id INTEGER REFERENCES text_lines ON DELETE CASCADE,
    position_start INTEGER NOT NULL,
    position_end INTEGER NOT NULL,
    PRIMARY KEY (sentence_id, text_line_id)
);

-- Add indexes for common query patterns
CREATE INDEX idx_sentence_text_lines_sentence ON sentence_text_lines(sentence_id);
CREATE INDEX idx_sentence_text_lines_line ON sentence_text_lines(text_line_id);

-- View for sentence context with line information
CREATE VIEW sentence_with_context AS
SELECT 
    s.id as sentence_id,
    s.content as sentence_content,
    s.categories as sentence_categories,
    tl.id as line_id,
    tl.line_number,
    tl.content as line_content,
    td.chapter,
    td.section,
    td.volume,
    t.title as text_title,
    t.reference_code as text_reference,
    a.name as author_name
FROM sentences s
JOIN sentence_text_lines stl ON s.id = stl.sentence_id
JOIN text_lines tl ON stl.text_line_id = tl.id
JOIN text_divisions td ON tl.division_id = td.id
JOIN texts t ON td.text_id = t.id
JOIN authors a ON t.author_id = a.id;
```

-- Add index on the view
CREATE INDEX idx_sentence_context_search ON sentence_with_context USING GIN (to_tsvector('english', sentence_content));

### Lemmas
```sql
CREATE TABLE lemmas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma TEXT NOT NULL,
    language_code VARCHAR(5),
    categories TEXT[],
    translations JSONB
);

CREATE INDEX idx_lemmas_lemma ON lemmas(lemma);
CREATE INDEX idx_lemmas_categories ON lemmas USING GIN(categories);
```

### Lemma Analyses
```sql
CREATE TABLE lemma_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma_id UUID REFERENCES lemmas ON DELETE CASCADE,
    analysis_text TEXT NOT NULL,
    analysis_data JSONB,
    citations JSONB,
    created_by TEXT NOT NULL
);
```

### Lexical Values
```sql
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
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_lexical_values_lemma ON lexical_values(lemma);
```

## JSONB Structures

### spacy_tokens (in text_lines)
```json
{
  "tokens": [
    {
      "text": "αἷμα",
      "lemma": "αἷμα",
      "pos": "NOUN",
      "tag": "N-",
      "dep": "nsubj",
      "morph": {}
    }
  ],
  "spans": [
    {
      "text": "αἷμα",
      "label": "Body Part",
      "start": 0,
      "end": 1
    }
  ]
}
```

### translations (in lemmas)
```json
{
  "EN": "blood",
  "AR": "دم",
  "GK": "αἷμα",
  "DE": "Blut"
}
```

### sentence_contexts (in lexical_values)
```json
{
  "sentence_id": {
    "text": "Full sentence text",
    "prev": "Previous sentence",
    "next": "Next sentence",
    "tokens": {
      "spacy_analysis": {}
    }
  }
}
```

### citations_used (in lexical_values)
```json
{
  "citations": [
    {
      "sentence": {
        "id": "sentence_id",
        "text": "sentence text"
      },
      "citation": "formatted citation",
      "context": {
        "line_id": "text_line_id",
        "line_text": "line content"
      },
      "location": {
        "volume": "vol",
        "chapter": "ch",
        "section": "sec"
      }
    }
  ]
}
```

## Key Features

1. **Hierarchical Text Storage**:
   - Authors -> Texts -> Text Divisions -> Text Lines
   - Each level maintains appropriate metadata and relationships

2. **Flexible Citation System**:
   - Supports both modern and traditional citation formats
   - Maintains author and work references
   - Handles structural components (volume, chapter, line, section)

3. **Rich Text Analysis**:
   - Sentence parsing and tracking
   - spaCy NLP integration
   - Category tagging at multiple levels

4. **Lexical Analysis**:
   - UUID-based lemma tracking
   - Multi-language support
   - LLM-generated analyses
   - Rich context storage

5. **Performance Optimizations**:
   - GIN indexes for array and JSONB fields
   - B-tree indexes for common lookups
   - Cascade deletes for maintaining referential integrity

## Common Queries

1. Finding text by citation:
```sql
SELECT tl.content 
FROM text_divisions td
JOIN text_lines tl ON td.id = tl.division_id
WHERE td.author_id_field = '[0086]' 
  AND td.work_number_field = '[055]';
```

2. Getting lemma analysis with context:
```sql
SELECT l.lemma, la.analysis_text, lv.sentence_contexts
FROM lemmas l
JOIN lemma_analyses la ON l.id = la.lemma_id
JOIN lexical_values lv ON l.lemma = lv.lemma
WHERE l.lemma = 'αἷμα';
```

3. Finding sentences by category:
```sql
SELECT s.content
FROM sentences s
WHERE 'Medical_Term' = ANY(s.categories);
```

## Next Steps

1. **Indexing Strategy**:
   - Monitor query patterns
   - Add/modify indexes based on performance needs
   - Consider partial indexes for common filters

2. **Data Migration**:
   - Plan incremental migration from existing data
   - Validate data integrity during migration
   - Maintain backup strategies

3. **Performance Monitoring**:
   - Set up query logging
   - Monitor JSONB field access patterns
   - Optimize common access paths

