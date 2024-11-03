"""
LLM prompt templates for SQL query generation.
"""

# Base query template with schema definition
QUERY_TEMPLATE = """
You are an AI assistant that generates SQL queries for a PostgreSQL database. 
The database contains ancient texts with the following schema:

WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
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
        ) as next_sentence
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number;

Important notes:
1. For searching in spacy_data JSON field, use: EXISTS (SELECT 1 FROM jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token WHERE ...)
2. For category searches, use: s.categories @> ARRAY[:category]::VARCHAR[]
3. For citation searches, use td.author_id_field and td.work_number_field
4. Always include the complete WITH clause and maintain the exact table structure and joins
5. Keep the ORDER BY clause as shown: division_id, min_line_number
6. For lemma searches, use: token->>'lemma' = :pattern
7. For text content searches, use: s.content ILIKE :pattern
8. For category searches, use: s.categories @> ARRAY[:category]::VARCHAR[]

Task: Generate a SQL query that answers this question: {question}

Only output the SQL query, no explanations or openings. 
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
        s.spacy_data as sentence_tokens,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
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
        ) as next_sentence
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id,
    LATERAL jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token
    WHERE token->>'lemma' = :pattern
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number;

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
        s.spacy_data as sentence_tokens,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
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
        ) as next_sentence
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
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number;

Only output the SQL query, no explanations.
"""
