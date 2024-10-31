# Database Queries Guide

This guide documents common query patterns for the Ancient Medical Texts database. All examples use SQLAlchemy syntax.

## Text Retrieval Queries

### 1. Find Text by Citation
```python
# Get text division by author and work reference
def get_text_by_citation(author_ref: str, work_ref: str) -> TextDivision:
    return (
        TextDivision.query
        .filter_by(
            author_id_field=author_ref,
            work_number_field=work_ref
        )
        .first()
    )

# Get all lines for a specific chapter
def get_chapter_lines(division_id: int, chapter: str) -> List[TextLine]:
    return (
        TextLine.query
        .join(TextDivision)
        .filter(
            TextDivision.id == division_id,
            TextDivision.chapter == chapter
        )
        .order_by(TextLine.line_number)
        .all()
    )
```

### 2. Search Text Content
```python
# Full-text search in lines
def search_text_content(query: str) -> List[TextLine]:
    return (
        TextLine.query
        .filter(TextLine.content.ilike(f"%{query}%"))
        .all()
    )

# Search by category
def search_by_category(category: str) -> List[TextLine]:
    return (
        TextLine.query
        .filter(TextLine.categories.contains([category]))
        .all()
    )
```

## Sentence Analysis Queries

### 1. Get Sentence Context
```python
# Get sentence with surrounding context
def get_sentence_context(sentence_id: int) -> Dict:
    sentence = Sentence.query.get(sentence_id)
    if not sentence:
        return None
        
    # Get surrounding sentences
    prev_sentence = (
        Sentence.query
        .filter(
            Sentence.id < sentence_id,
            Sentence.source_line_ids.overlap(sentence.source_line_ids)
        )
        .order_by(Sentence.id.desc())
        .first()
    )
    
    next_sentence = (
        Sentence.query
        .filter(
            Sentence.id > sentence_id,
            Sentence.source_line_ids.overlap(sentence.source_line_ids)
        )
        .order_by(Sentence.id)
        .first()
    )
    
    return {
        "text": sentence.content,
        "prev": prev_sentence.content if prev_sentence else "",
        "next": next_sentence.content if next_sentence else "",
        "spacy_data": sentence.spacy_data
    }
```

### 2. Find Sentences by Category
```python
# Get all sentences with specific category
def get_sentences_by_category(category: str) -> List[Sentence]:
    return (
        Sentence.query
        .filter(Sentence.categories.contains([category]))
        .all()
    )

# Get sentences with multiple categories
def get_sentences_by_categories(categories: List[str]) -> List[Sentence]:
    return (
        Sentence.query
        .filter(Sentence.categories.overlap(categories))
        .all()
    )
```

## Lexical Analysis Queries

### 1. Lemma Queries
```python
# Get lemma with all analyses
def get_lemma_with_analyses(lemma: str) -> Dict:
    result = (
        Lemma.query
        .filter_by(lemma=lemma)
        .options(
            joinedload(Lemma.analyses)
        )
        .first()
    )
    
    if not result:
        return None
        
    return {
        "lemma": result.lemma,
        "translations": result.translations,
        "categories": result.categories,
        "analyses": [
            {
                "text": analysis.analysis_text,
                "data": analysis.analysis_data,
                "citations": analysis.citations
            }
            for analysis in result.analyses
        ]
    }

# Find related lemmas by category
def get_related_lemmas(category: str) -> List[Lemma]:
    return (
        Lemma.query
        .filter(Lemma.categories.contains([category]))
        .all()
    )
```

### 2. Lexical Value Queries
```python
# Get lexical value with all contexts
def get_lexical_value(lemma: str) -> Dict:
    value = (
        LexicalValue.query
        .filter_by(lemma=lemma)
        .options(
            joinedload(LexicalValue.sentence)
            .joinedload(Sentence.text_lines)
            .joinedload(TextLine.division)
        )
        .first()
    )
    
    if not value:
        return None
        
    return {
        "lemma": value.lemma,
        "translation": value.translation,
        "descriptions": {
            "short": value.short_description,
            "long": value.long_description
        },
        "contexts": value.sentence_contexts,
        "citations": value.citations_used
    }

# Get all lexical values for a category
def get_lexical_values_by_category(category: str) -> List[LexicalValue]:
    return (
        LexicalValue.query
        .join(Sentence)
        .filter(Sentence.categories.contains([category]))
        .all()
    )
```

## Citation Queries

### 1. Get Citations by Reference
```python
# Get all citations for a specific work
def get_work_citations(author_ref: str, work_ref: str) -> List[Dict]:
    divisions = (
        TextDivision.query
        .filter_by(
            author_id_field=author_ref,
            work_number_field=work_ref
        )
        .all()
    )
    
    return [
        {
            "citation": division.format_citation(),
            "location": {
                "volume": division.volume,
                "chapter": division.chapter,
                "section": division.section
            }
        }
        for division in divisions
    ]
```

### 2. Find Citations in Analyses
```python
# Get all analyses citing a specific work
def get_analyses_with_citation(author_ref: str, work_ref: str) -> List[Dict]:
    return (
        LemmaAnalysis.query
        .filter(
            LemmaAnalysis.citations.contains({
                "source": {
                    "author_id": author_ref,
                    "work_id": work_ref
                }
            })
        )
        .all()
    )
```

## Performance Optimization

### 1. Efficient Joins
```python
# Efficient loading of text hierarchy
def get_text_hierarchy(text_id: int) -> Dict:
    text = (
        Text.query
        .options(
            joinedload(Text.author),
            joinedload(Text.divisions)
            .joinedload(TextDivision.lines)
        )
        .get(text_id)
    )
    
    return {
        "author": text.author.name,
        "title": text.title,
        "divisions": [
            {
                "citation": div.format_citation(),
                "lines": [line.content for line in div.lines]
            }
            for div in text.divisions
        ]
    }
```

### 2. Pagination
```python
# Paginated text line retrieval
def get_paginated_lines(
    division_id: int,
    page: int = 1,
    per_page: int = 20
) -> Dict:
    query = TextLine.query.filter_by(division_id=division_id)
    
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        "items": pagination.items,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page
    }
```

## Common Query Patterns

### 1. Category-based Queries
```python
# Base query for category filtering
def category_filter(query, category: str):
    return query.filter(
        or_(
            TextLine.categories.contains([category]),
            Sentence.categories.contains([category]),
            Lemma.categories.contains([category])
        )
    )
```

### 2. Full-text Search
```python
# Combined text search across multiple tables
def full_text_search(query: str) -> Dict:
    return {
        "lines": TextLine.query.filter(TextLine.content.ilike(f"%{query}%")).all(),
        "sentences": Sentence.query.filter(Sentence.content.ilike(f"%{query}%")).all(),
        "lemmas": Lemma.query.filter(Lemma.lemma.ilike(f"%{query}%")).all()
    }
```

### 3. Cached Queries
```python
# Cache common queries using Redis
@cache.memoize(timeout=300)
def get_cached_text_division(author_ref: str, work_ref: str) -> TextDivision:
    return get_text_by_citation(author_ref, work_ref)
```

## Error Handling

```python
def safe_query(query_func):
    @wraps(query_func)
    def wrapper(*args, **kwargs):
        try:
            return query_func(*args, **kwargs)
        except SQLAlchemyError as e:
            log.error(f"Database error in {query_func.__name__}: {str(e)}")
            raise DatabaseError(f"Error executing query: {str(e)}")
    return wrapper
```

## Next Steps

1. **Query Optimization**:
   - Monitor query performance
   - Add indexes based on common patterns
   - Implement caching for frequent queries

2. **Error Handling**:
   - Implement comprehensive error handling
   - Add retry logic for transient failures
   - Set up monitoring for slow queries

3. **Documentation**:
   - Document new query patterns
   - Update performance recommendations
   - Maintain query examples
