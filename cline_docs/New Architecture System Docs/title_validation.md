# Title Validation in Citation Processing

## Overview

Title validation ensures the integrity and correctness of title processing across the citation pipeline. This document outlines current and planned validation checks.

## Current Validation

### 1. Title Format Validation

```python
# Valid title formats
-Z//641a/t	{TITLE}      # Basic title
-Z//641a/t1	{PART 1}     # Numbered title part
-Z//t/2	{PART 2}         # Just title marker
```

### 2. Basic Checks
- Title marker presence (t, t1, t2)
- Title number format
- Basic content validation

## Planned Validation Improvements

### 1. Title Part Sequence Validation

```python
class TitleValidator:
    def validate_sequence(self, parts: Dict[str, str]) -> List[str]:
        """Validate title part sequence."""
        errors = []
        numbers = sorted(int(n) for n in parts.keys())
        
        # Check for gaps
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append("Title sequence has gaps")
            
        # Check for duplicates
        if len(set(numbers)) != len(numbers):
            errors.append("Duplicate title numbers found")
            
        return errors
```

### 2. Division Boundary Validation

```python
def validate_division_boundaries(self, titles: List[Citation]) -> List[str]:
    """Ensure titles stay within their divisions."""
    errors = []
    current_division = None
    
    for title in titles:
        division = self._get_division_key(title)
        if current_division and division != current_division:
            if title.title_number != "1":
                errors.append(f"Title sequence crosses division boundary: {division}")
        current_division = division
        
    return errors
```

### 3. Content Format Validation

```python
def validate_title_content(self, content: str) -> List[str]:
    """Validate title content format."""
    errors = []
    
    # Check for balanced braces
    if content.count('{') != content.count('}'):
        errors.append("Unbalanced braces in title")
        
    # Check for nested titles
    if '{' in content[content.find('{')+1:]:
        errors.append("Nested title markers found")
        
    return errors
```

### 4. Title State Validation

```python
def validate_title_state(self, citation: Citation) -> List[str]:
    """Validate title state consistency."""
    errors = []
    
    # Check title flags consistency
    if citation.is_title and not citation.title_number:
        errors.append("Title flag set but no title number")
        
    # Check title parts consistency
    if citation.title_parts and not citation.is_title:
        errors.append("Title parts present but not marked as title")
        
    # Check complete title
    if citation.title_text and not citation.title_parts.get("1"):
        errors.append("Title text present but no parts stored")
        
    return errors
```

## Implementation Plan

### Phase 1: Basic Validation
- [x] Title marker validation
- [x] Title number format
- [x] Basic content checks

### Phase 2: Sequence Validation
- [ ] Title part sequence checks
- [ ] Division boundary validation
- [ ] Part number consistency

### Phase 3: Content Validation
- [ ] Content format validation
- [ ] Nested title detection
- [ ] Character encoding checks

### Phase 4: State Validation
- [ ] Title state consistency
- [ ] Cross-reference validation
- [ ] Division state checks

## Error Handling

### 1. Validation Errors
```python
class TitleValidationError(Exception):
    """Custom exception for title validation errors."""
    def __init__(self, message: str, details: List[str]):
        self.message = message
        self.details = details
        super().__init__(self.message)
```

### 2. Error Recovery
```python
def recover_from_validation_error(self, error: TitleValidationError) -> None:
    """Attempt to recover from validation errors."""
    if "sequence" in error.message:
        self._fix_sequence_gaps()
    elif "boundary" in error.message:
        self._reset_title_state()
    elif "content" in error.message:
        self._sanitize_content()
```

### 3. Error Reporting
```python
def report_validation_issues(self, errors: List[str]) -> None:
    """Report validation issues to logging system."""
    for error in errors:
        logger.error(f"Title validation error: {error}")
        if self.report:
            self.report.add_title_issue(error)
```

## Best Practices

### 1. Validation Timing
- Validate during parsing
- Validate before joining parts
- Validate after division changes

### 2. Error Recovery
- Attempt to fix minor issues
- Log all validation attempts
- Maintain data consistency

### 3. Performance
- Cache validation results
- Validate only when needed
- Use efficient checks

### 4. Testing
- Test all validation cases
- Include edge cases
- Test error recovery

## Future Enhancements

### 1. Enhanced Validation
- Smarter sequence validation
- Better boundary detection
- Content pattern matching

### 2. Recovery Mechanisms
- Automatic sequence fixing
- Content normalization
- State recovery

### 3. Reporting
- Detailed validation reports
- Error statistics
- Recovery success rates

### 4. Integration
- IDE validation support
- Real-time validation
- Batch validation tools
