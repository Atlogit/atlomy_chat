"""
SQL queries specific to corpus manager functionality.
Separate from citation queries to maintain clear separation of concerns.
"""

# Base query for corpus search operations
CORPUS_SEARCH_QUERY = """
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        tl.id as line_id,
        tl.content as line_text,
        ARRAY_AGG(tl.line_number) as line_numbers,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.volume,
        td.chapter,
        td.section,
        -- Get previous and next sentences for context
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
    WHERE {where_clause}
    GROUP BY 
        s.id, s.content,
        tl.id, tl.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number
"""

# Specific search queries
CORPUS_TEXT_SEARCH = CORPUS_SEARCH_QUERY.format(
    where_clause="s.content ILIKE :pattern"
)

# Updated lemma search to find all occurrences per line
CORPUS_LEMMA_SEARCH = """
WITH line_matches AS (
    SELECT DISTINCT ON (tl.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        tl.id as line_id,
        tl.content as line_text,
        ARRAY_AGG(tl.line_number) as line_numbers,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.volume,
        td.chapter,
        td.section,
        -- Get previous and next sentences for context
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
        tl.id, tl.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM line_matches
ORDER BY division_id, min_line_number
"""

CORPUS_CATEGORY_SEARCH = CORPUS_SEARCH_QUERY.format(
    where_clause="s.categories @> ARRAY[:category]::VARCHAR[]"
)
