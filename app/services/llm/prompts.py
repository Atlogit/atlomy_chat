"""
LLM prompt templates for SQL query generation.
"""

# Base query template with schema definition
QUERY_TEMPLATE = """
You are an AI that generates SQL queries for a PostgreSQL database containing ancient texts with NLP annotations, metadata, and structured text information. The database schema is as follows:

### Database Schema:
- **`sentences`**: Stores individual sentences with categories and NLP data in `spacy_data`.
  - `id`: Unique identifier for each sentence.
  - `content`: The text of the sentence.
  - `categories`: Array of categories (e.g., "Topography").
  - `spacy_data`: JSON containing token information (e.g., `tokens` array with fields such as `text`, `pos`, `lemma`, and `category`).

- **`sentence_text_lines`**: Links sentences to text lines.
  - `sentence_id`: Foreign key referencing `sentences`.
  - `text_line_id`: Foreign key referencing `text_lines`.

- **`text_lines`**: Represents lines in the text.
  - `id`: Unique identifier for each line.
  - `line_number`: Position of the line in the text.
  - `division_id`: Foreign key referencing `text_divisions`.

- **`text_divisions`**: Represents divisions of a work (e.g., chapters).
  - `id`: Unique identifier.
  - `text_id`: Foreign key referencing `texts`.
  - `author_name`, `work_name`: Details of the text's division.
  - `volume`, `chapter`, `section`: Citation information.

- **`texts`**: Metadata about the overall text.
  - `id`: Unique identifier for the text.
  - `title`: Title of the work.
  - `author_id`: Foreign key to `authors`.

- **`authors`**: Stores author information.
  - `id`: Unique identifier for the author.
  - `name`: Name of the author.

### Query Instructions:
1. **`spacy_data` JSON**: `spacy_data` holds a `tokens` array, each token a JSON object with:
   - `text` (original token),
   - `lemma` (base form),
   - `pos` (part of speech),
   - `category` (semantic category).
   
   Queries should support filtering on multiple fields in `spacy_data` (e.g., category and part of speech) using `jsonb_array_elements`. Filter tokens to meet all specified criteria (e.g., `category` = "Topography" and `pos` = "NOUN").

2. **Text content matching**: Use case-insensitive matches with wildcards (`ILIKE '%' || :param || '%'`) for flexible text matching in author and category fields.

3. **General structure**: Use a `WITH` clause for the main query logic, joining necessary tables as shown, and ordering results by citation. Return fields like `sentence_id`, `sentence_text`, `sentence_tokens`, and citation details.

### SQL Query Template:
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data->'tokens' as sentence_tokens,
        array_agg(tl.line_number ORDER BY tl.line_number) as line_numbers,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.author_id_field,
        td.work_number_field,
        td.volume,
        td.chapter,
        td.section,
        LAG(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as prev_sentence,
        LEAD(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as next_sentence,
        tl.content as line_text
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id
    WHERE EXISTS (
        SELECT 1
        FROM jsonb_array_elements(s.spacy_data::jsonb->'tokens') AS token
        WHERE token->>'category' ILIKE '%Topography%'
        AND token->>'pos' = '%NOUN%'
    )
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        td.author_id_field, td.work_number_field,
        t.title, a.name,
        td.volume, td.chapter, td.section,
        tl.content
)
SELECT * FROM sentence_matches
ORDER BY division_id, line_numbers[1];

### Task:
Generate a SQL query to answer this question: {question}
Only return the SQL query, with no additional explanations or commentary.
"""

# Template for specialized lemma search
LEMMA_QUERY_TEMPLATE = """
Generate a SQL query to find all occurrences of the lemma '{lemma}' in the sentences table.
Include citation information from text_divisions and texts tables.

Use this schema:
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data->'tokens' as sentence_tokens,
        array_agg(tl.line_number ORDER BY tl.line_number) as line_numbers,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.author_id_field,
        td.work_number_field,
        td.volume,
        td.chapter,
        td.section,
        LAG(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as prev_sentence,
        LEAD(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as next_sentence,
        tl.content as line_text
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id,
    LATERAL json_array_elements(s.spacy_data->'tokens') AS token
    WHERE token->>'lemma' = :pattern
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        td.author_id_field, td.work_number_field,
        t.title, a.name,
        td.volume, td.chapter, td.section,
        tl.content
)
SELECT * FROM sentence_matches
ORDER BY division_id, line_numbers[1];

Only output the SQL query, no explanations.
"""

# Template for category search
CATEGORY_QUERY_TEMPLATE = """
Generate a SQL query to find all sentences in the category '{category}'.
Include citation information and group by text/division.

Use this schema:
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data->'tokens' as sentence_tokens,
        array_agg(tl.line_number ORDER BY tl.line_number) as line_numbers,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.author_id_field,
        td.work_number_field,
        td.volume,
        td.chapter,
        td.section,
        LAG(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as prev_sentence,
        LEAD(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as next_sentence,
        tl.content as line_text
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id
    WHERE s.categories @> ARRAY['{category}']::VARCHAR[]
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        td.author_id_field, td.work_number_field,
        t.title, a.name,
        td.volume, td.chapter, td.section,
        tl.content
)
SELECT * FROM sentence_matches
ORDER BY division_id, line_numbers[1];

Only output the SQL query, no explanations.
"""
