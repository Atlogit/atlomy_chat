# Sentence Parsing Implementation Guide

## Overview
This document details how sentences are formed while preserving line numbers and citations based on dynamic work structures from TLG indexes.

## Current Status

### Working Components
- Work structure lookup ✓
- Basic sentence formation ✓
- Token mapping ✓
- NLP processing ✓
- Line number preservation ✓
- Hyphenated word joining ✓
- Sentence boundary detection ✓

### Key Changes
```python
# Sentences are now formed directly from their source lines
sentences.append(Sentence(
    content=sentence_text,
    source_lines=current_lines.copy(),  # Include all contributing lines
    citation=getattr(current_lines[0], 'citation', None),
    structure=None
))

# Example output:
"Ὤμου δὲ ἄρθρον ἕνα τρόπον οἶδα ὀλισθάνον, τὸν ἐς τὴν μασχάλην·"
Source lines: [Line 1, Line 2]  # Properly tracks hyphenated word across lines
```

## Key Components

### 1. Line Processing
```python
# Each line maintains its own citation and line number
parser_line = ParserTextLine(
    content=line.content.strip(),
    citation=citation,
    line_number=line.line_number,
    is_title=line.is_title if hasattr(line, 'is_title') else False
)
```

### 2. Sentence Formation
```python
# Add line to current sentence
if current_sentence and current_sentence[-1].endswith('-'):
    # Join hyphenated word
    current_sentence[-1] = current_sentence[-1][:-1]
    current_sentence.append(content)
else:
    # Add space if needed
    if current_sentence and self._should_add_space(current_sentence[-1], content):
        current_sentence.append(' ')
    current_sentence.append(content)

# Always add line to source lines
current_lines.append(line)
```

### 3. Sentence Boundary Detection
```python
# Look for sentence endings in complete text
while True:
    end_pos = self._find_sentence_end(current_text)
    if end_pos is None:
        break
        
    # Extract sentence text
    sentence_text = current_text[:end_pos].strip()
    
    # Create sentence with all contributing lines
    sentences.append(Sentence(
        content=sentence_text,
        source_lines=current_lines.copy(),
        citation=getattr(current_lines[0], 'citation', None),
        structure=None
    ))
```

## Processing Flow

### 1. Line Processing
- Each line processed independently ✓
- Citations preserved per line ✓
- Line numbers maintained ✓

### 2. Sentence Formation
- Proper word spacing between lines ✓
- Hyphenated word joining ✓
- Source line tracking ✓
- Sentence boundary detection ✓

### 3. Citation Handling
- Citations preserved per line ✓
- Line numbers maintained ✓
- Title citations handled separately ✓

## Examples

1. Basic Sentence:
```
Input Lines:
.1.1    Ὤμου δὲ ἄρθρον ἕνα τρόπον...
.1.2    σχάλην· ἄνω δὲ οὐδέποτε...

Result:
- Sentence: "Ὤμου δὲ ἄρθρον ἕνα τρόπον... σχάλην·"
- Source Lines: [Line 1, Line 2]
- Line Numbers: [1, 2]
```

2. Hyphenated Word:
```
Input:
Line 1: "τὸν ἐς τὴν μα-"
Line 2: "σχάλην·"

Result:
- Joined correctly: "τὸν ἐς τὴν μασχάλην·"
- Source lines preserved: [Line 1, Line 2]
```

## Best Practices

1. **Line Processing**
   - Process each line independently
   - Preserve line numbers and citations
   - Handle hyphenation properly

2. **Sentence Formation**
   - Track all contributing lines
   - Handle word spacing correctly
   - Detect sentence boundaries accurately

3. **Error Handling**
   - Validate line content
   - Check for missing citations
   - Log parsing issues

## Testing

1. Test sentence boundaries:
   - Period (.)
   - Interpunct (·)
   - Mixed punctuation

2. Test line joining:
   - Hyphenated words
   - Word spacing
   - Punctuation handling

3. Test source line tracking:
   - Multiple lines per sentence
   - Line number preservation
   - Citation preservation

## Related Documentation
- [Sentence Processing Flow](sentence_processing_flow.md)
- [Citation Parsing Enhancements](Citation_Parsing_Enhancements_Handoff.md)
- [Division Handling Guide](division_handling_guide.md)
