"""
LLM prompt templates for lexical value generation.
"""

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
