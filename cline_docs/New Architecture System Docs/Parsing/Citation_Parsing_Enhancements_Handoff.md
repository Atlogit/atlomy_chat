### Citation Parsing Enhancements - Implementation Details

#### 1. Dynamic Citation Patterns

The system now generates citation patterns dynamically based on work structure:

```python
# For work structure ["Section", "Line"]
pattern = r"^\.(\d+)\.(\d+)"  # Matches .1.2
groups = ["section", "line"]

# For work structure ["Book", "Chapter", "Line"]
pattern = r"^\.(\d+)\.(\d+)\.(\d+)"  # Matches .1.2.3
groups = ["book", "chapter", "line"]
```

#### 2. Current Issues

##### A. Pattern Matching Not Working
```python
# Current Issue
DEBUG:toolkit.migration.line_processor:Created default citation for division 1 line None using structure ['Section', 'line']: {'section': '1'}

# Pattern not matching basic citations like:
.1.1    Ὤμου δὲ ἄρθρον...
.1.2    σχάλην· ἄνω...
```

##### B. Line Number Extraction
- Line numbers not being extracted from citations
- Default citations created without line numbers
- Structure found but not properly used

#### 3. Solutions Needed

##### A. Pattern Generation (CorpusCitation)
```python
def _get_citation_pattern(self, author_id: str, work_id: str):
    # Get work structure
    structure = self.citation_parser.get_work_structure(author_id, work_id)
    if not structure:
        return None
        
    # Create pattern based on structure
    pattern_parts = [r"^"]  # Start with dot
    groups = []
    
    # Need to fix pattern generation here
    for level in structure:
        level_name = level.lower()
        pattern_parts.append(r"\.(\d+)")  # Add capture group
        groups.append(level_name)
```

##### B. Citation Parsing
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
            
            # Need to fix hierarchy level extraction
            for group, value in zip(pattern["groups"], match.groups()):
                citation.hierarchy_levels[group] = value
                setattr(citation, group, value)
                
            return citation
```

##### C. Line Number Extraction
```python
def _get_line_number_from_citation(self, content: str, division: TextDivision):
    # Parse citation using work structure
    remaining, citations = self.corpus_citation.parse_citation(
        content,
        author_id=division.author_id_field,
        work_id=division.work_number_field
    )
    
    if citations:
        citation = citations[0]
        structure = self._get_division_structure(division)
        if structure:
            # Need to fix line level extraction
            for level in structure:
                if level.lower() == 'line':
                    line_value = citation.hierarchy_levels.get(level.lower())
                    if line_value:
                        return int(line_value)
```

#### 4. Required Changes

1. Pattern Generation:
   - Fix pattern to match basic citations
   - Handle alpha suffixes properly
   - Maintain proper structure

2. Line Number Handling:
   - Extract line numbers correctly
   - Handle alpha suffixes
   - Preserve in hierarchy_levels

3. Citation Creation:
   - Use structure properly
   - Set all hierarchy levels
   - Handle title citations

4. Examples to Support:
```python
# Basic citations
".1.2" -> Citation(section="1", line="2")

# Alpha-suffixed citations
"1.345a.4" -> Citation(book="1", chapter="345a", line="4")

# Title citations
".t.1" -> Citation(title_number="1")
```

#### 5. Testing Notes

Test with various structures:
- Section.Line works
- Book.Chapter.Line works
- Book.Chapter.Section.Line works
- Title citations
- Mixed Greek/citation text
- Alpha-suffixed citations

Verify:
- Pattern generation
- Line number extraction
- Citation hierarchy
- Structure preservation

#### 6. Future Improvements

1. Pattern Optimization:
   - Cache common patterns
   - Validate structure formats
   - Add pattern validation

2. Error Handling:
   - Structure validation
   - Pattern matching errors
   - Line number conversion

3. Performance:
   - Pattern compilation
   - Structure caching
   - Citation creation

#### 7. Related Documentation
- [Division Handling Guide](division_handling_guide.md)
- [Sentence Parsing Guide](sentence_parsing_handover.md)
- [Merged Architecture Overview](Merged_Architecture_Overview.md)
