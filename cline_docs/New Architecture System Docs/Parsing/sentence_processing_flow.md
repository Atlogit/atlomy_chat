# Text Processing Flow: From Raw Content to Searchable Sentences

## Example Text
Using this excerpt from De articulis:
```
-Z//1/1    Ὤμου δὲ ἄρθρον ἕνα τρόπον οἶδα ὀλισθάνον, τὸν ἐς τὴν μα-
-Z//1/2    σχάλην· ἄνω δὲ οὐδέποτε εἶδον, οὐδὲ ἐς τὸ ἔξω·
```

## Processing Steps

### 1. Initial Text Loading (corpus_text.py)
```python
# Each line is processed independently with its citation
parser_lines = [
    ParserTextLine(
        content="Ὤμου δὲ ἄρθρον ἕνα τρόπον οἶδα ὀλισθάνον, τὸν ἐς τὴν μα-",
        line_number=1,
        citation=Citation(author_id="0627", work_id="010", hierarchy_levels={'line': '1'})
    ),
    ParserTextLine(
        content="σχάλην· ἄνω δὲ οὐδέποτε εἶδον, οὐδὲ ἐς τὸ ἔξω·",
        line_number=2,
        citation=Citation(author_id="0627", work_id="010", hierarchy_levels={'line': '2'})
    )
]
```

### 2. Sentence Formation (sentence_parser.py)
```python
# Build sentence text while tracking source lines
current_sentence = []
current_lines = []

# Handle hyphenated word
if current_sentence and current_sentence[-1].endswith('-'):
    current_sentence[-1] = current_sentence[-1][:-1]  # Remove hyphen
    current_sentence.append(content)
else:
    # Add space if needed
    if current_sentence:
        current_sentence.append(' ')
    current_sentence.append(content)

# Track source lines
current_lines.append(line)

# Create sentence when boundary found
sentences.append(Sentence(
    content=''.join(current_sentence),
    source_lines=current_lines.copy(),
    citation=getattr(current_lines[0], 'citation', None)
))
```

### 3. Sentence Boundary Detection
```python
def _find_sentence_end(self, text: str) -> Optional[int]:
    """Find the end position of a sentence in text."""
    match = self.sentence_end_pattern.search(text)
    if match:
        return match.end()
    return None

# Results in sentences:
1. "Ὤμου δὲ ἄρθρον ἕνα τρόπον οἶδα ὀλισθάνον, τὸν ἐς τὴν μασχάλην·"
   Source lines: [Line 1, Line 2]
2. "ἄνω δὲ οὐδέποτε εἶδον, οὐδὲ ἐς τὸ ἔξω·"
   Source lines: [Line 2]
```

### 4. NLP Processing
```python
# Process complete sentence with spaCy
doc = nlp_pipeline.nlp(sentence.content)

# Extract token information and categories
processed_doc = {
    "text": doc.text,
    "tokens": [
        {
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "category": ", ".join(span.label_ for span in doc.spans.get("sc", [])
                                if span.start <= token.i < span.end)
        }
        for token in doc
    ]
}
```

### 5. Database Storage
```sql
-- 1. Store text lines with their original content and line numbers
INSERT INTO text_lines (id, content, line_number, spacy_tokens) VALUES
(1, 'Ὤμου δὲ ἄρθρον...', 1, '{tokens: [...]}'),
(2, 'σχάλην· ἄνω δὲ...', 2, '{tokens: [...]}');

-- 2. Store complete sentences
INSERT INTO sentences (id, content, spacy_data) VALUES
(1, 'Ὤμου δὲ ἄρθρον... μασχάλην·', '{tokens: [...]}');

-- 3. Link sentences to their source lines
INSERT INTO sentence_text_lines 
(sentence_id, text_line_id, position_start, position_end) VALUES
(1, 1, 0, 46),
(1, 2, 0, 8);
```

## Key Components

### TextLine Model
- Stores individual lines with their content and line numbers
- Preserves original citation data
- Contains spaCy NLP analysis for the line's tokens

### Sentence Model
- Stores complete sentences that may span multiple lines
- Links to all contributing source lines
- Contains full spaCy NLP analysis

### sentence_text_lines Association Table
- Maps sentences to their source lines
- Stores character positions within each line
- Enables accurate citation tracking

### SentenceParser
- Handles sentence boundary detection
- Manages proper word joining across lines
- Maintains source line tracking
- Preserves citation data

## Benefits of This Architecture

1. Accurate Line Numbers
   - Each line maintains its own line number
   - Hyphenated words preserve both source lines
   - Citations show correct line ranges

2. Proper Sentence Formation
   - Sentences end at valid boundaries (. or ·)
   - Words joined correctly across lines
   - Proper spacing between words

3. Citation Preservation
   - Each line keeps its citation data
   - Sentences track all source lines
   - Line numbers preserved throughout

4. Flexible Retrieval
   - Can show individual lines or complete sentences
   - Accurate citation information
   - Support for both exact and lemmatized search

## Example Queries

1. Get sentence with source lines:
```sql
SELECT s.content, array_agg(tl.line_number ORDER BY tl.line_number)
FROM sentences s
JOIN sentence_text_lines stl ON s.id = stl.sentence_id
JOIN text_lines tl ON stl.text_line_id = tl.id
WHERE s.id = 1
GROUP BY s.id, s.content;

Result:
content: "Ὤμου δὲ ἄρθρον... μασχάλην·"
line_numbers: [1, 2]
```

2. Find sentences containing a word:
```sql
SELECT s.content, array_agg(DISTINCT tl.line_number)
FROM sentences s
JOIN sentence_text_lines stl ON s.id = stl.sentence_id
JOIN text_lines tl ON stl.text_line_id = tl.id
WHERE s.spacy_data->>'tokens' @> '[{"text": "μασχάλην"}]'
GROUP BY s.id, s.content;
