# Sentence Processing Flow

## Overview

This document explains how the system handles text processing at the sentence level, particularly focusing on how it maintains accuracy when dealing with sentences that span multiple lines or when single lines contain parts of multiple sentences. It also details how citations are handled within this flow.

## Processing Flow

### 1. Line to Sentence Reconstruction
- Lines are first grouped into complete sentences using `SentenceParser`
- The parser handles:
  - Sentences spanning multiple lines
  - Lines containing parts of multiple sentences
  - Special cases like quotations and abbreviations

### 2. Complete Sentence Processing
- Each reconstructed complete sentence is processed through the NLP pipeline
- This ensures linguistic analysis is performed on grammatically complete units
- Maintains context and relationships between words
- Stores spaCy analysis data for efficient citation lookup

### 3. Token Mapping
The `_map_tokens_to_line` method precisely maps processed tokens back to their source lines:
```python
def _map_tokens_to_line(self, line_content: str, processed_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Map tokens from a processed sentence to a specific line's content."""
    # Maps tokens based on character position
    # Ensures each line gets only its relevant tokens
    # Handles special cases like hyphenation
```

### 4. Citation Handling
The system now handles citations directly at the sentence level:
- Citations are retrieved using direct sentence queries
- No LLM processing needed for simple lemma lookups
- Position information is maintained through sentence_text_lines
- Full sentence context (prev/next) is preserved

#### Citation Flow
1. **Citation Request**
   - System receives request for citations of a lemma
   - Direct query to sentences table using spacy_data
   - No LLM query generation needed

2. **Context Retrieval**
   - Gets complete sentence containing the lemma
   - Retrieves previous and next sentences
   - Maintains line position information

3. **Citation Formation**
   - Formats citation with author and work information
   - Includes volume, chapter, and section data
   - Preserves line number references

## Example Scenario

Consider this text split across lines:
```
Line 1: "This is the first"
Line 2: "sentence. And this is"
Line 3: "the second sentence."
```

### Processing Steps:

1. **Sentence Reconstruction**:
   - First sentence: "This is the first sentence."
   - Second sentence: "And this is the second sentence."

2. **NLP Processing**:
   - Each complete sentence is processed independently
   - Full linguistic context is maintained
   - spaCy analysis stored for citation lookup

3. **Token Mapping**:
   - Line 1 receives: tokens for "This is the first"
   - Line 2 receives: tokens for both "sentence" and "And this is"
   - Line 3 receives: tokens for "the second sentence"

4. **Citation Storage**:
   - Sentences table stores complete sentences
   - sentence_text_lines maintains position mapping
   - Enables efficient citation retrieval

## Data Storage

### Sentence Level
- Complete sentence content
- spaCy analysis data
- Category information
- Source line references

### Line Level
- Original line content
- Line number and position
- Division references
- Token mappings

### Relationship Tracking
- sentence_text_lines association table
- Position tracking (start/end)
- Line to sentence mapping
- Division hierarchy preservation

## Key Benefits

1. **Accuracy**:
   - Complete sentences ensure proper linguistic analysis
   - Precise token mapping maintains line-level granularity
   - No data loss in complex cases

2. **Efficiency**:
   - Direct sentence-based citation lookup
   - No LLM processing for simple citations
   - Optimized database queries

3. **Flexibility**:
   - Handles various text formats and structures
   - Accommodates different line breaking patterns
   - Supports complex sentence structures

4. **Citation Quality**:
   - Full sentence context preserved
   - Accurate position information
   - Rich metadata availability

## Implementation Details

### SentenceParser
- Reconstructs complete sentences from lines
- Handles special cases and punctuation
- Maintains reference to source lines

### NLPPipeline
- Processes complete sentences
- Generates comprehensive token analysis
- Provides linguistic features and relationships

### CitationHandler
- Direct sentence-based lookups
- Efficient context retrieval
- Rich citation formatting

## Best Practices

1. **Text Processing**:
   - Always process complete sentences
   - Maintain line-level granularity
   - Handle special cases explicitly

2. **Data Management**:
   - Store tokens at line level
   - Preserve sentence relationships
   - Maintain bidirectional traceability

3. **Citation Handling**:
   - Use direct sentence queries when possible
   - Preserve full context
   - Maintain position information

## Future Considerations

1. **Optimization**:
   - Enhanced token mapping algorithms
   - Improved special case handling
   - Better performance for large texts

2. **Features**:
   - Support for more complex sentence structures
   - Enhanced linguistic analysis
   - Better handling of edge cases

3. **Monitoring**:
   - Advanced error tracking
   - Processing statistics
   - Quality metrics

4. **Citation Enhancement**:
   - Additional context options
   - More citation formats
   - Enhanced metadata support
