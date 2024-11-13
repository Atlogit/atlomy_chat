# Title Handling in Citation Processing

## Overview

The system handles title citations in ancient texts, supporting both single-line and multiline titles. Titles are processed within their parent divisions (page/chapter/etc) and can have multiple numbered parts.

## Citation Formats

```
# Single line title
-Z//641a/t	{TITLE TEXT}      # Title line 1 in page 641a
-Z//641b/t2	{TITLE PART 2}    # Title line 2 in page 641b

# Multiline title
-Z//t/1	{FIRST LINE}          # First line of title
-Z//t/2	{SECOND LINE}         # Second line of title

# Regular lines
-Z//641a/36	Regular text...   # Line 36 in page 641a
-Z//641b/1	More text...      # Line 1 in page 641b
```

## Component Roles

### 1. Citation Class (citation_types.py)
- Stores title data (number, text, parts)
- Provides methods for managing title parts
- Joins parts into complete titles

```python
@dataclass
class Citation:
    title_number: Optional[str] = None    # From t1, t2, etc.
    title_text: Optional[str] = None      # Complete title
    title_parts: Dict[str, str] = field(default_factory=dict)
    is_title: bool = False
```

### 2. Citation Parser (citation_parser.py)
- Identifies title markers (t, t1, t2)
- Extracts title content
- Creates Citation objects with title flags

```python
def _analyze_citation_format(self, text: str) -> Tuple[int, Optional[str], Optional[str], Optional[str]]:
    """Returns (num_fields, title_marker, line_number, title_content)."""
    # Example: -Z//641a/t2 {TITLE} -> (1, "t2", None, "TITLE")
```

### 3. Citation Processor (citation_processor.py)
- Uses Citation's title methods
- Manages title completion
- Preserves title content

```python
def _store_title_part(self, citation: Citation, content: str) -> None:
    """Store title part using Citation's methods."""
    citation.add_title_part(content, citation.title_number)
```

### 4. Text Module (corpus_text.py)
- Uses processor for title handling
- Updates division title_text
- Maintains division boundaries

```python
# Handle title parts using citation processor
if parser_line.is_title and line_citation.is_title:
    self.citation_processor._store_title_part(citation, parser_line.content)
    complete_title = self.citation_processor._get_complete_title(citation)
    if complete_title:
        division.title_text = complete_title
```

## Processing Flow

1. Parser identifies title citation:
   - Extracts title marker (t, t1, t2)
   - Sets title flags and numbers
   - Preserves title content

2. Citation object stores title info:
   - Maintains title parts dictionary
   - Tracks title numbers
   - Provides methods for joining parts

3. Processor manages completion:
   - Stores title parts in Citation
   - Retrieves complete titles
   - Preserves division boundaries

4. Text module updates divisions:
   - Gets complete titles from processor
   - Updates division title_text
   - Maintains proper structure

## Future Improvements

1. Title Validation
   - Verify title part sequence (no gaps)
   - Check for duplicate title numbers
   - Validate title content format

2. Enhanced Title Processing
   - Support for nested titles
   - Handle cross-references in titles
   - Title content normalization

3. Division Handling
   - Smarter division boundary detection
   - Better handling of title-only divisions
   - Title inheritance across divisions

4. Error Recovery
   - Handle missing title parts
   - Recover from out-of-order parts
   - Better error reporting

5. Performance
   - Cache frequently accessed titles
   - Optimize title part joining
   - Batch title updates

6. Testing
   - Add specific title test cases
   - Test multiline title scenarios
   - Test division boundary cases

## Example Usage

```python
# Create citation with title
citation = Citation(
    author_id="0627",
    work_id="010",
    is_title=True,
    title_number="1"
)

# Add title parts
citation.add_title_part("First line", "1")
citation.add_title_part("Second line", "2")

# Get complete title
complete_title = citation.get_complete_title()
# Result: "First line Second line"
```

## Best Practices

1. Title Storage
   - Always use Citation's title methods
   - Don't store title state elsewhere
   - Preserve title part order

2. Division Boundaries
   - Keep titles within their divisions
   - Reset title state at division boundaries
   - Properly handle page/chapter changes

3. Error Handling
   - Log title processing issues
   - Provide clear error messages
   - Maintain data consistency

4. Performance
   - Only join titles when needed
   - Clear title parts after joining
   - Use appropriate data structures
