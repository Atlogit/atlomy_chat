"""
LLM prompt templates for various tasks.
"""

# Template for lexical value analysis
LEXICAL_VALUE_TEMPLATE = """
You are an AI assistant specializing in ancient Greek lexicography and philology. You will build a lexical value based on validated texts analysis on a PhD level. Analyze the following word or lemma and its usage in the given citations.

Word to analyze (lemma): 
{word}

Citations:
{citations}

Task: Based on these citations, provide:
1. A concise translation of the word.
2. A short description (up to 2000 words) of its meaning and usage. This is a summary of the long description.
3. A longer, more detailed description.
4. A list of related terms or concepts.
5. A list of citations you used in the short or long descriptions

Formatting Instructions:
1. Your response must be a valid JSON object.
2. For all text fields (translation, short_description, long_description):
   - Replace any newlines with \\n
   - Replace any quotes with \\"
   - Remove any control characters
   - Use proper JSON string escaping
3. For arrays (related_terms, citations_used):
   - Each element should be a simple string
   - No special characters or line breaks in array elements
   - For citations_used, use the full citation format as provided in the input
     Example: "Galenus Med., De sanitate tuenda libri vi, Volume 6: Chapter 135: Lines 12-15"
4. Ensure the entire response is one continuous JSON object
5. Test that your JSON is valid before completing the response

Required JSON Format:
{{
    "lemma": "{word}",
    "translation": "Your single-line translation here",
    "short_description": "Your single-paragraph description here",
    "long_description": "Your longer description here with \\n for line breaks",
    "related_terms": ["term1", "term2", "term3"],
    "citations_used": ["Full citation 1", "Full citation 2"]
}}

Content Guidelines:
- The description should include information derived from text analysis
- Cover meaning, usage, notable connotations, context
- Note any contradictions or variations in usage
- If citations are provided:
  * Reference them in the text to support claims using the standard abbreviated format
  * Use accustomed abbreviations
  * Include full citations in citations_used exactly as they appear in the input
- If no citations are provided, use your expertise in ancient Greek
- Do not make up citations or use external resources
- Only use provided citations to support your analysis

Remember: All text must be properly escaped JSON. No raw line breaks or quotes.
"""

# Template for term analysis
ANALYSIS_TEMPLATE = """
You are an expert in ancient medical texts analysis.
    
Term to analyze: {term}

Here are the contexts where this term appears:

{context_str}

Please provide a comprehensive analysis of this term, including:
1. Its meaning and usage in medical contexts
2. Any variations in meaning across different texts or authors
3. The medical concepts or theories it relates to
4. Its significance in ancient medical thought

Format your response as a scholarly analysis, citing specific examples from the provided contexts.
"""

# Template for SQL query generation
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
    WHERE EXISTS (
        SELECT 1 
        FROM jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token 
        WHERE token->>'category' IS NOT NULL AND token->>'category' != ''
    )
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number;

Important notes:
1. ALWAYS include the complete WITH clause when writing queries
2. For searching in spacy_data JSON field, use: EXISTS (SELECT 1 FROM jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token WHERE ...)
3. Use array operators (@>) for searching in sentences.categories with proper type casting
4. For category searches, use: s.categories @> ARRAY[:category]::VARCHAR[]
5. For citation searches, use td.author_id_field and td.work_number_field
6. Always include GROUP BY and ORDER BY clauses as shown in the template
7. Never reference the sentence_matches CTE without first defining it in a WITH clause
8. Always maintain the exact table structure and joins as shown in the template
9. Keep the ORDER BY clause simple: division_id, min_line_number

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
    LEFT JOIN authors a ON t.author_id = a.id
    WHERE EXISTS (
        SELECT 1 
        FROM jsonb_array_elements(CAST(s.spacy_data->'tokens' AS jsonb)) AS token 
        WHERE token->>'lemma' = '{lemma}'
    )
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
