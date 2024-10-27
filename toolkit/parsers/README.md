# Text Processing Toolkit - Parsers

This package provides a set of parsers for processing ancient medical texts, maintaining both the original structure and enabling analysis through sentence-based processing.

## Components

### 1. Citation Parser (`citation.py`)
Handles parsing and formatting of citation references in ancient texts.

#### Supported Citation Formats:
- TLG References: `[0057][001][1][2]` (author, work, division, subdivision)
- Volume References: `128.32.5` (volume, chapter, line)
- Title References: `.t.1` (title number)

```python
from toolkit.parsers.citation import CitationParser

parser = CitationParser()
text = "[0057][001][1][2] Some text"
remaining, citation = parser.parse_citation(text)
print(str(citation))  # "[0057][001][1][2]"
```

### 2. Text Parser (`text.py`)
Handles text extraction and line-based processing while preserving citations.

Features:
- UTF-8/Latin-1 encoding support
- Line continuation handling
- Citation inheritance across lines
- Special character normalization

```python
from toolkit.parsers.text import TextParser

parser = TextParser()
lines = await parser.parse_file("text.txt")
for line in lines:
    print(f"Content: {line.content}")
    if line.citation:
        print(f"Citation: {line.citation}")
```

### 3. Sentence Parser (`sentence.py`)
Converts line-based text into sentences while maintaining references to original lines and citations.

Features:
- Splits on . and · delimiters
- Maintains line references
- Preserves citation information
- Handles sentences across line breaks

```python
from toolkit.parsers.sentence import SentenceParser

parser = SentenceParser()
sentences = await parser.parse_lines(lines)
for sentence in sentences:
    print(f"Sentence: {sentence.content}")
    print(f"From lines: {[line.content for line in sentence.source_lines]}")
```

## Complete Processing Pipeline

The parsers work together to provide a complete text processing pipeline:

1. Text Parser extracts and cleans text, handling citations
2. Sentence Parser converts lines into analysis-ready sentences
3. Original structure and citations are preserved throughout

Example usage:

```python
from toolkit.parsers import TextParser, SentenceParser

async def process_text(file_path):
    # Initialize parsers
    text_parser = TextParser()
    sentence_parser = SentenceParser()
    
    # Process text
    lines = await text_parser.parse_file(file_path)
    sentences = await sentence_parser.parse_lines(lines)
    
    # Analyze sentences
    for sentence in sentences:
        print(f"\nSentence: {sentence.content}")
        citations = sentence_parser.get_sentence_citations(sentence)
        print(f"Citations: {[str(c) for c in citations]}")
```

## Configuration

### Citation Parser Configuration
Citations patterns can be customized through a JSON configuration file:

```json
{
  "citation_patterns": [
    {
      "pattern": "\\[(\\d{4})\\]\\s+\\[(\\d{3})\\]\\s+\\[(.*?)\\]\\s+\\[(.*?)\\]",
      "groups": ["author_id", "work_id", "division", "subdivision"],
      "format": "{author_name}, {work_name} ({division}{subdivision})"
    }
  ]
}
```

Pass the configuration file path when creating the parser:
```python
parser = CitationParser(config_path="citation_config.json")
```

## Error Handling

The toolkit provides specific exceptions for different error types:

```python
from toolkit.parsers.exceptions import (
    ParsingError,
    TextExtractionError,
    CitationError,
    EncodingError
)

try:
    lines = await text_parser.parse_file(file_path)
except TextExtractionError as e:
    print(f"Error extracting text: {e}")
except EncodingError as e:
    print(f"Encoding error: {e}")
```

## Best Practices

1. **File Handling**
   - Always use UTF-8 encoding when possible
   - Handle encoding fallback for legacy files

2. **Citation Processing**
   - Configure citation patterns based on your text corpus
   - Use citation inheritance for multi-line sections

3. **Sentence Analysis**
   - Consider sentence boundaries in your specific texts
   - Use sentence metadata for analysis

4. **Error Handling**
   - Catch specific exceptions for better error handling
   - Log parsing issues for later review

## See Also

- `examples.py` - Complete examples of parser usage
- Test files in `tests/parsers/` for more usage examples
