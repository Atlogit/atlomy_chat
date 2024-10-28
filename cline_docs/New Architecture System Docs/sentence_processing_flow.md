# Sentence Processing Flow

## Overview

This document explains how the system handles text processing at the sentence level, particularly focusing on how it maintains accuracy when dealing with sentences that span multiple lines or when single lines contain parts of multiple sentences.

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

### 3. Token Mapping
The `_map_tokens_to_line` method precisely maps processed tokens back to their source lines:
```python
def _map_tokens_to_line(self, line_content: str, processed_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Map tokens from a processed sentence to a specific line's content."""
    # Maps tokens based on character position
    # Ensures each line gets only its relevant tokens
    # Handles special cases like hyphenation
```

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

3. **Token Mapping**:
   - Line 1 receives: tokens for "This is the first"
   - Line 2 receives: tokens for both "sentence" and "And this is"
   - Line 3 receives: tokens for "the second sentence"

## Data Storage

- Each line maintains its own `spacy_tokens` field in the database
- Token mapping ensures no data loss when lines contain multiple sentence parts
- Position-based mapping guarantees accurate token assignment

## Key Benefits

1. **Accuracy**:
   - Complete sentences ensure proper linguistic analysis
   - Precise token mapping maintains line-level granularity
   - No data loss in complex cases

2. **Flexibility**:
   - Handles various text formats and structures
   - Accommodates different line breaking patterns
   - Supports complex sentence structures

3. **Data Integrity**:
   - Preserves original line-based structure
   - Maintains complete linguistic analysis
   - Ensures traceable token-to-line mapping

## Implementation Details

### SentenceParser
- Reconstructs complete sentences from lines
- Handles special cases and punctuation
- Maintains reference to source lines

### NLPPipeline
- Processes complete sentences
- Generates comprehensive token analysis
- Provides linguistic features and relationships

### Token Mapping
- Position-based token assignment
- Handles special cases (e.g., hyphenation)
- Ensures accurate token-to-line correlation

## Best Practices

1. **Text Processing**:
   - Always process complete sentences
   - Maintain line-level granularity
   - Handle special cases explicitly

2. **Data Management**:
   - Store tokens at line level
   - Preserve sentence relationships
   - Maintain bidirectional traceability

3. **Error Handling**:
   - Log processing anomalies
   - Handle edge cases gracefully
   - Maintain data consistency

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
