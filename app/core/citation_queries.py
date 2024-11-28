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
        s.spacy_data->'tokens' as sentence_tokens,  -- Extract just the tokens array
        array_agg(DISTINCT tl.line_number ORDER BY tl.line_number) as line_numbers,  -- Get all unique line numbers
        td.id as division_id,
        -- Source fields
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.author_id_field,
        td.work_number_field,
        td.work_abbreviation_field,
        td.author_abbreviation_field,
        -- Location fields (ordered to match CitationLocation)
        td.epistle,
        td.fragment,
        td.volume,
        td.book,
        td.chapter,
        td.section,
        td.page,
        -- Line is handled through line_numbers array
        -- Get previous and next sentences for context
        LAG(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as prev_sentence,
        LEAD(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as next_sentence,
        string_agg(tl.content, ' ' ORDER BY tl.line_number) as line_text
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id
    {join_clause}
    WHERE {where_clause}
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        td.author_id_field, td.work_number_field,
        td.work_abbreviation_field, td.author_abbreviation_field,
        t.title, a.name,
        td.epistle, td.fragment, td.volume, td.book,
        td.chapter, td.section, td.page
)
SELECT * FROM sentence_matches
ORDER BY division_id, line_numbers[1]
"""

# Query for lemma search using spacy_data JSON field with direct token access
LEMMA_CITATION_QUERY = CITATION_QUERY.format(
    join_clause=", LATERAL json_array_elements(s.spacy_data->'tokens') AS token",
    where_clause="token->>'lemma' = :pattern"
)

# Query for text content search
TEXT_CITATION_QUERY = CITATION_QUERY.format(
    join_clause="",
    where_clause="s.content ILIKE :pattern"
)

# Query for category search
CATEGORY_CITATION_QUERY = CITATION_QUERY.format(
    join_clause="",
    where_clause="(s.categories @> ARRAY[:category]::VARCHAR[] OR tl.categories @> ARRAY[:category]::VARCHAR[])"
)

# Query for citation search by author and work
CITATION_SEARCH_QUERY = CITATION_QUERY.format(
    join_clause="",
    where_clause="td.author_id_field = :author_id AND td.work_number_field = :work_number"
)
