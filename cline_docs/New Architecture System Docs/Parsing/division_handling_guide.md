# Division Handling in Citation Processing

## Overview
This document outlines how divisions and citations are handled dynamically based on work structures from TLG indexes.

## Current Status

### 1. Working Components
- Structure lookup from TLG indexes
- Basic pattern generation
- Metadata extraction
- Title citation handling

### 2. Current Issues
```python
# Line numbers not being extracted
DEBUG:toolkit.migration.line_processor:Created default citation for division 1 line None using structure ['Section', 'line']: {'section': '1'}

# Pattern not matching basic citations
.1.1    Ὤμου δὲ ἄρθρον...
.1.2    σχάλην· ἄνω...
```

## Work Structure Handling

### 1. Structure Lookup
```python
# Get structure from TLG indexes
structure = citation_parser.get_work_structure(
    division.author_id_field,
    division.work_number_field
)  # e.g., ["Section", "Line"] or ["Book", "Chapter", "Line"]
```

### 2. Dynamic Pattern Generation
```python
# Create pattern based on structure
pattern_parts = [r"^"]  # Start with dot
groups = []

for level in structure:
    level_name = level.lower()
    pattern_parts.append(r"\.(\d+)")  # Add capture group
    groups.append(level_name)
    
pattern = "".join(pattern_parts)
# For ["Section", "Line"] -> "^\.(\d+)\.(\d+)"
# For ["Book", "Chapter", "Line"] -> "^\.(\d+)\.(\d+)\.(\d+)"
```

### 3. Citation Mapping
```python
# Map citation parts to structure levels
citation.hierarchy_levels = {}
for group, value in zip(pattern["groups"], match.groups()):
    citation.hierarchy_levels[group] = value
    setattr(citation, group, value)
```

## Module Responsibilities

### 1. CorpusCitation (corpus_citation.py)
- Generates patterns from work structure
- Parses citations using dynamic patterns
- Creates citations with proper hierarchy
```python
def parse_citation(self, content: str, author_id: str, work_id: str):
    # Get work-specific pattern
    pattern = self._get_citation_pattern(author_id, work_id)
    if pattern:
        match = pattern["regex"].match(content)
        if match:
            citation = Citation(
                author_id=author_id,
                work_id=work_id
            )
            # Map groups to hierarchy levels
            for group, value in zip(pattern["groups"], match.groups()):
                citation.hierarchy_levels[group] = value
```

### 2. LineProcessor (line_processor.py)
- Gets line numbers based on structure
- Creates citations with proper levels
- Handles title citations
```python
def _get_line_number_from_citation(self, content: str, division: TextDivision):
    remaining, citations = self.corpus_citation.parse_citation(
        content,
        division.author_id_field,
        division.work_number_field
    )
    if citations:
        citation = citations[0]
        structure = self._get_division_structure(division)
        for level in structure:
            if level.lower() == 'line':
                line_value = citation.hierarchy_levels.get(level.lower())
                return int(line_value)
```

### 3. SentenceProcessor (sentence_processor.py)
- Maps lines by structure-based numbers
- Maintains line order in sentences
```python
def _get_sentence_lines(self, sentence: Sentence, db_lines: List[DBTextLine]):
    # Map lines by structure-based line numbers
    db_line_map = {}
    for db_line in db_lines:
        line_num = self._get_line_number(db_line)
        if line_num is not None:
            db_line_map[line_num] = db_line
```

## Citation Flow

1. Structure Lookup:
   - Get work structure from TLG indexes ✓
   - Cache structure for efficiency ✓
   - Use structure for pattern generation ✗

2. Pattern Generation:
   - Create regex pattern from structure ✗
   - Map groups to structure levels ✗
   - Handle title citations separately ✓

3. Citation Parsing:
   - Use work-specific pattern ✗
   - Map groups to hierarchy levels ✗
   - Extract line numbers from correct level ✗

4. Line Processing:
   - Parse citations using work structure ✗
   - Extract line numbers from hierarchy ✗
   - Create parser text lines ✓

5. Sentence Formation:
   - Map lines by structure-based numbers ✓
   - Maintain line order in sentences ✓
   - Track line positions ✓

## Examples

1. Section.Line Work (e.g., [0627][010]):
```
Structure: ["Section", "Line"]
Pattern: ^\.(\d+)\.(\d+)
Input: .1.2
Result: Citation(section="1", line="2")
```

2. Book.Chapter.Line Work:
```
Structure: ["Book", "Chapter", "Line"]
Pattern: ^\.(\d+)\.(\d+)\.(\d+)
Input: .1.2.3
Result: Citation(book="1", chapter="2", line="3")
```

3. Title Citations:
```
Pattern: ^\.t\.(\d+)
Input: .t.1
Result: Citation(title_number="1")
```

## Best Practices

1. **Structure Handling**
   - Always get from TLG indexes
   - Cache structures for efficiency
   - Validate structure format

2. **Pattern Generation**
   - Generate based on structure
   - Cache patterns per work
   - Handle all structure formats

3. **Line Numbers**
   - Extract from correct level
   - Validate before conversion
   - Preserve in hierarchy

4. **Error Handling**
   - Validate structures
   - Handle missing patterns
   - Log parsing failures

## Common Issues

1. **Structure Mismatch**
   - Problem: Wrong pattern generated
   - Solution: Validate against indexes

2. **Line Numbers**
   - Problem: Wrong level used
   - Solution: Check structure position

3. **Citation Format**
   - Problem: Pattern doesn't match
   - Solution: Generate from structure

## Future Improvements

1. Structure Validation:
   - Check against TLG indexes
   - Validate level names
   - Handle variations

2. Pattern Optimization:
   - Improve pattern generation
   - Add pattern validation
   - Enhance caching

3. Error Recovery:
   - Better structure fallbacks
   - Pattern matching errors
   - Line number handling

## Related Documentation
- [Citation Parsing Enhancements](Citation_Parsing_Enhancements_Handoff.md)
- [Sentence Parsing Guide](sentence_parsing_handover.md)
- [Merged Architecture Overview](Merged_Architecture_Overview.md)
