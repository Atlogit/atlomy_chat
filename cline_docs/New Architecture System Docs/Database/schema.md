# Database Schema Design

## Core Tables

### Editions
```sql
CREATE TABLE editions (
    id SERIAL PRIMARY KEY,
    type VARCHAR(10),          -- 'early' or 'modern'
    name TEXT,
    title TEXT,
    editor_name TEXT,
    year_of_publish TEXT,
    publisher TEXT
);
```

### Texts
```python
CREATE TABLE texts (
    id SERIAL PRIMARY KEY,
    edition_id INTEGER REFERENCES editions,
    reference_code VARCHAR(20), -- [0057]
    title TEXT,
    author TEXT,
    treatise TEXT,
    century TEXT
);
```

### Text Division

```python
CREATE TABLE text_divisions (
    id SERIAL PRIMARY KEY,
    text_id INTEGER REFERENCES texts,
    book_number TEXT,
    chapter_number TEXT,
    section_number TEXT,
    page_number INTEGER,
    column TEXT,
    -- Early edition parallels
    early_chapter TEXT,
    early_section TEXT,
    early_page INTEGER,
    early_column TEXT,
    jones_chapter_number TEXT
);
```

### Text Lines

```python
CREATE TABLE text_lines (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES text_divisions,
    line_number INTEGER,
    content TEXT,
    word TEXT,
    word_before TEXT,
    word_after TEXT,
    quote TEXT,
    -- Early parallels
    early_line_number INTEGER,
    early_word TEXT,
    early_word_before TEXT,
    early_word_after TEXT,
    early_quote TEXT,
    -- NLP data
    spacy_tokens JSONB,
    -- Flags
    is_modern_primary BOOLEAN,
    is_early_primary BOOLEAN
);
```

### Lemmas

```python
CREATE TABLE lemmas (
    id SERIAL PRIMARY KEY,
    lemma TEXT,
    lemma_arabic TEXT,
    source_language VARCHAR(5),
    category_types TEXT[],
    translations JSONB,
    descriptions JSONB,
    functions JSONB
);
```


## JSONB Structures

### spacy_tokens

```python
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

### Translations

```python
{
  "EN": "blood",
  "AR": "دم",
  "GK": "αἷμα",
  "DE": "Blut"
}
```

### descriptions

```python
{
  "long": {
    "EN": "detailed description...",
    "AR": "..."
  },
  "short": {
    "EN": "brief description",
    "AR": "..."
  }
}
```

## Indexes

```python
-- Text search
CREATE INDEX idx_text_content ON text_lines USING gin(to_tsvector('greek', content));

-- JSONB indexes
CREATE INDEX idx_spacy_spans ON text_lines USING gin((spacy_tokens->'spans'));
CREATE INDEX idx_lemma_translations ON lemmas USING gin(translations);

-- Common lookups
CREATE INDEX idx_reference_code ON texts(reference_code);
CREATE INDEX idx_lemma_text ON lemmas(lemma);
```

## Constraints
```python
-- Unique constraints
ALTER TABLE texts ADD CONSTRAINT unique_reference_code 
    UNIQUE (reference_code);

ALTER TABLE lemmas ADD CONSTRAINT unique_lemma 
    UNIQUE (lemma, source_language);

-- Check constraints
ALTER TABLE editions ADD CONSTRAINT valid_edition_type 
    CHECK (type IN ('early', 'modern'));
```

Next Steps
Review Query Patterns
Understand the Migration Strategy
Implement using the Toolkit Guide