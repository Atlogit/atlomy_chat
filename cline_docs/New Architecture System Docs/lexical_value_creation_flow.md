# Lexical Value Creation Flow

## Overview
The lexical value creation tool is a core feature that analyzes ancient medical terms using LLM technology and citation context. This document outlines the implementation approach in the new architecture.

## Components and Flow

### 1. Citation Handling
```python
class TextDivision(Base):
    """Model for storing text divisions with enhanced citation components."""
    
    # Citation components
    author_id_field: Mapped[str] = mapped_column(String, nullable=False)
    work_number_field: Mapped[str] = mapped_column(String, nullable=False)
    author_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    def format_citation(self) -> str:
        """Format a full citation string using author and work names."""
        author = self.author_name or f"[{self.author_id_field}]"
        work = self.work_name or f"[{self.work_number_field}]"
        
        citation = f"{author}, {work}"
        
        # Add structural components
        components = []
        if self.volume:
            components.append(f"Volume {self.volume}")
        if self.chapter:
            components.append(f"Chapter {self.chapter}")
        if self.line:
            components.append(f"Line {self.line}")
            
        if components:
            citation += f" ({', '.join(components)})"
            
        return citation
```

### 2. API Layer (`app/api/lexical.py`)
```python
@router.post("/create")
async def create_lexical_value(
    data: LexicalCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new lexical value entry."""
    lexical_service = LexicalService(db)
    task_id = f"create_{data.lemma}_{time.time()}"
    background_tasks.add_task(
        lexical_service.create_lexical_entry,
        data.lemma,
        data.search_lemma,
        task_id
    )
    return {"task_id": task_id, "status": "processing"}
```

### 3. Service Layer (`app/services/lexical_service.py`)
```python
class LexicalService:
    async def _get_citations(self, word: str, search_lemma: bool) -> List[Dict[str, Any]]:
        """Get citations with proper author and work names."""
        try:
            # Query to get sentences containing the word/lemma
            if search_lemma:
                query = """
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
                    WHERE CAST(s.spacy_tokens AS TEXT) ILIKE :pattern
                )
                SELECT * FROM matched_sentences
                """
                pattern = f'%"lemma":"{word}"%'
            else:
                # Similar query for word search
                ...

            result = await self.session.execute(text(query), {"pattern": pattern})
            citations = []
            
            for row in result.mappings():
                division = await self.get_text_division(row['division_id'])
                citation = {
                    "sentence": row["sentence_text"],
                    "citation": division.format_citation(),
                    "context": {
                        "line_id": row["line_id"],
                        "line_numbers": row["line_numbers"]
                    },
                    "location": {
                        "volume": row["volume"],
                        "chapter": row["chapter"],
                        "section": row["section"]
                    }
                }
                citations.append(citation)

            return citations

        except Exception as e:
            logger.error(f"Error getting citations for {word}: {str(e)}")
            raise
```

### 4. LLM Integration (`app/services/llm_service.py`)
```python
class LLMService:
    lexical_term_template = """
    You are an AI assistant specializing in ancient Greek lexicography and philology. You will build a lexical value based on validated texts analysis on a PhD level. Analyze the following word or lemma and its usage in the given citations.
    
    Word to analyze (lemma): 
    {word}
    
    Citations:
    {citations}  # Now includes properly formatted author and work names
    
    Task: Based on these citations, provide:
    1. A concise translation of the word.
    2. A short description (up to 2000 words) of its meaning and usage.
    3. A longer, more detailed description.
    4. A list of related terms or concepts.
    5. A list of citations you used in the descriptions
    
    When citing sources in your descriptions, use the full citation format provided.
    Example: "As described in Hippocrates Med., Prognosticon (Chapter 2, Lines 10-15)..."
    """
```

## Data Flow

1. **Citation Retrieval**
   - Query matches sentences containing lemma/word
   - Join with text_divisions to get author and work names
   - Format citations using proper names and structural components

2. **LLM Processing**
   - Send properly formatted citations to LLM
   - LLM uses full citation format in analysis
   - Validate response structure and content

3. **Storage**
   - Store lexical value with enhanced citations
   - Cache results with proper citation format
   - Update references with structured citation data

## Key Improvements

1. **Enhanced Citations**
   - Full author and work names instead of ID numbers
   - Consistent citation formatting
   - Better readability for users and LLM

2. **Database Integration**
   - Author and work names stored in text_divisions
   - Efficient querying and joins
   - Proper indexing for performance

3. **Service Layer**
   - Enhanced citation retrieval
   - Proper formatting methods
   - Consistent citation handling

4. **LLM Integration**
   - Better context with proper citations
   - Improved analysis quality
   - More accurate references

## Migration Notes

1. **Database Updates**
   - Added author_name and work_name fields
   - Populated from TLG indexes
   - Created proper indexes

2. **Code Updates**
   - Enhanced TextDivision model
   - Updated service layer
   - Modified LLM templates

3. **Testing**
   - Citation formatting
   - Name resolution
   - LLM integration
   - Performance impact

## Usage Example

```python
# Example lexical value with enhanced citations
{
    "lemma": "φλέψ",
    "translation": "vein, blood vessel",
    "short_description": "In Hippocrates Med., Prognosticon (Chapter 2, Lines 10-15), the term φλέψ refers to...",
    "long_description": "The anatomical understanding of φλέψ is detailed in Galen Med., De Anatomicis Administrationibus (Book 7, Chapter 3)...",
    "related_terms": ["αἷμα", "ἀρτηρία"],
    "citations_used": [
        {
            "sentence": "...",
            "citation": "Hippocrates Med., Prognosticon (Chapter 2, Lines 10-15)",
            "context": {...}
        }
    ]
}


## Migration Notes

1. **Data Migration**
   - Create migration scripts for existing lexical values
   - Preserve all citation data and references
   - Validate data integrity during migration

2. **API Compatibility**
   - Maintain backward compatibility where possible
   - Document any breaking changes
   - Provide migration guides for frontend updates

3. **Testing Strategy**
   - Unit tests for each component
   - Integration tests for the complete flow
   - Performance testing under load
   - Validation error testing
   - Edge case handling

## Error Handling Strategy

1. **Validation Errors**
   - Required fields missing
   - Invalid JSON structure
   - Malformed data

2. **Processing Errors**
   - LLM service failures
   - Database connection issues
   - Cache failures

3. **Recovery Procedures**
   - Automatic retries for transient failures
   - Graceful degradation
   - Clear error messages
   - Detailed logging

4. **Error Response Format**
```json
{
    "status": "error",
    "code": "ERROR_TYPE",
    "message": "Detailed error message",
    "details": {
        "field": "Additional error context",
        "suggestion": "Potential fix or workaround"
    }
}

