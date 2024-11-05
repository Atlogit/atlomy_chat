"""
Shared SQL queries for citation handling.
Used across services to ensure consistent citation formatting.
"""

# Base query for getting citations with sentence context
CITATION_QUERY = """
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        array_agg(tl.line_number ORDER BY tl.line_number) as line_numbers,
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
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, line_numbers[1]
"""

# Direct sentence query for efficient lemma lookups
DIRECT_SENTENCE_QUERY = """
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        array_agg(tl.line_number ORDER BY tl.line_number) as line_numbers,
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
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, line_numbers[1]
"""

# Query for lemma search using spacy_data JSON field
LEMMA_CITATION_QUERY = CITATION_QUERY.format(
    where_clause="EXISTS (SELECT 1 FROM jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token WHERE token->>'lemma' = :pattern)"
)

# Query for text content search
TEXT_CITATION_QUERY = CITATION_QUERY.format(
    where_clause="s.content ILIKE :pattern"
)

# Query for category search
CATEGORY_CITATION_QUERY = CITATION_QUERY.format(
    where_clause="s.categories @> ARRAY[:category]::VARCHAR[]"
)

# Query for citation search by author and work
CITATION_SEARCH_QUERY = CITATION_QUERY.format(
    where_clause="td.author_id_field = :author_id AND td.work_number_field = :work_number"
)
