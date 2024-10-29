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
        tl.spacy_tokens as sentence_tokens,
        tl.id as line_id,
        tl.content as line_text,
        tl.line_number,
        td.id as division_id,
        td.author_name,
        td.work_name,
        td.volume,
        td.chapter,
        td.section,
        -- Get previous and next sentences for context
        LAG(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY tl.line_number
        ) as prev_sentence,
        LEAD(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY tl.line_number
        ) as next_sentence,
        -- Group line numbers for the sentence
        array_agg(tl.line_number) OVER (
            PARTITION BY s.id
        ) as line_numbers
    FROM sentences s
    JOIN text_lines tl ON s.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    WHERE {where_clause}
)
SELECT * FROM sentence_matches
WHERE array_length(line_numbers, 1) > 0
ORDER BY division_id, line_number
"""

# Query for lemma search
LEMMA_CITATION_QUERY = CITATION_QUERY.format(
    where_clause="CAST(tl.spacy_tokens AS TEXT) ILIKE :pattern"
)

# Query for text content search
TEXT_CITATION_QUERY = CITATION_QUERY.format(
    where_clause="s.content ILIKE :pattern"
)

# Query for category search
CATEGORY_CITATION_QUERY = CITATION_QUERY.format(
    where_clause="tl.categories @> ARRAY[CAST(:category AS VARCHAR)]::VARCHAR[]"
)

# Query for citation search by author and work
CITATION_SEARCH_QUERY = CITATION_QUERY.format(
    where_clause="td.author_id_field = :author_id AND td.work_number_field = :work_number"
)
