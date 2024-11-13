# Validation Changes Documentation

## Recent Updates (November 2024)

### Line Number Handling

1. Citation Parser Changes
- Added line number handling for title markers (t1, t2)
- Improved tab content handling in citations
- Enhanced line number extraction from hierarchy levels

2. Database Layer Updates
- Modified line number conversion in corpus_db.py
- Added integer validation for line numbers
- Improved error handling for non-numeric values

3. Text Processing Updates
- Added sequential line numbering fallback
- Enhanced title marker line number handling
- Improved line continuity validation

### Known Issues

1. Line Continuity
- Some divisions show line number gaps
- Example: Expected line 10, found 9
- Potential cause: Title markers affecting line numbering

2. Citation Processing
- Some citations missing line numbers
- Title markers need consistent line number handling
- Tab content in citations needs standardization

### Required Changes

1. Citation Processor
- Review line number handling in citation_processor.py
- Ensure proper inheritance of line numbers
- Handle title markers consistently

2. Content Validator
- Update line continuity validation
- Consider title markers in validation
- Add more detailed validation reporting

3. Testing Needed
- Test with various citation formats
- Verify line number handling in title markers
- Check line continuity across divisions

### Implementation Details

1. Line Number Handling
```python
# Clean line number from citation
if line_value:
    clean_value = line_value.split('\t')[0] if '\t' in line_value else line_value
    try:
        line_number = int(clean_value)
    except (ValueError, TypeError):
        pass
```

2. Title Marker Processing
```python
# Handle title markers
if is_title or title_marker:
    citation.is_title = True
    if title_number:
        clean_title = title_number.split('\t')[0]
        citation.title_number = clean_title
        citation.hierarchy_levels['line'] = clean_title
```

### Next Steps

1. Immediate Tasks
- Review citation_processor.py line number handling
- Fix line continuity validation
- Add tests for different citation formats

2. Future Improvements
- Add better error reporting
- Enhance validation logging
- Improve title marker handling

3. Documentation Updates
- Add more code examples
- Document common issues
- Update validation rules

### Migration Impact

1. Data Changes
- Line numbers now consistently integer
- Title markers preserve line numbers
- Better handling of tab content

2. Validation Rules
- Updated line continuity checks
- Enhanced title marker validation
- Improved error reporting

### Technical Notes

1. Citation Format
```
-Z//639a/t1	              {ΠΕΡΙ ΖΩΙΩΝ ΜΟΡΙΩΝ}
-Z//639a/t2	                            {Α}
-Z//639a/1	  Περὶ πᾶσαν θεωρίαν τε καὶ μέθοδον...
```

2. Line Number Rules
- Must be integer
- Sequential within division
- Titles affect numbering
- Tab separates citation from content

### Validation Rules

1. Line Continuity
- Check sequential line numbers
- Handle title markers
- Report gaps in sequence

2. Citation Format
- Validate structure
- Check line numbers
- Verify title markers

3. Content Rules
- Non-empty content
- Valid line numbers
- Proper title handling

### Error Handling

1. Common Issues
- Invalid line numbers
- Missing line numbers
- Line continuity gaps

2. Resolution Steps
- Clean line values
- Convert to integers
- Use sequential fallback

### Future Considerations

1. Improvements
- Better error reporting
- Enhanced validation
- Automated testing

2. Documentation
- Update examples
- Add troubleshooting
- Document edge cases
