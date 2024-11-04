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
2. A short description of its meaning and usage, particularly in a medical context. This is a summary of the long description.
3. A longer, detailed description an full analysis The analysis shoul be up to 2000 words.
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

An example of a finalized lexcial value:
{{
"lemma": "μετέωρος, -ον",
"translation": "Raised, high, suspended",
"short_description": "The term is a composite of the preposition μετά and the verb ἀείρω and literally means \"raised above\". Depending on the context, it may be translated as \"raised\", \"suspended\", \"high\", \"on the surface\", or metaphorically as \"uncertain\" or \"pending\". \n\nWhen referring to anatomical structures, it often means \"unsupported\" (e.g., Gal. AA 4.10, 469 Garofalo = 2.469 K – about a muscle not fixed to or resting on another) or hanging (Hipp. Fract. 7.31-34 – about using a sling to prevent the forearm from hanging).\n\nIn physiology, it can mean \"shallow\", particularly in relation to breathing (Gal. Diff. Resp., 7.946 K) or \"superficial\" (e.g., about pain: Hipp. Aph. 6.7 564 L.). However, when used in the context of the digestive system, it may mean inflated, unsettled (Hipp. Aph. 4.73 528 L., 5.64 556 L.).",
"long_description": "The term is a composite of the preposition μετά and the verb ἀείρω and literally means \"raised above\". Depending on the context, it may be translated as \"raised\", \"suspended\", \"high\", \"on the surface\", or metaphorically as \"uncertain\" or \"pending\".\n\nWhen referring to anatomical structures, it often means \"unsupported\" (e.g., Gal. AA 4.10, 469 Garofalo = 2.469 K – about a muscle not fixed to or resting on another) or hanging (Hipp. Fract. 7, Jouanna 14,11 = 3.445 L. – about using a sling to prevent the forearm from hanging).\n\nIn physiology, it can mean \"shallow\", particularly in relation to breathing (Gal. Diff. Resp., 7.946 K.) or \"superficial\" (e.g., about pain: Hipp. Aph. 6.7 564 L.). However, when used in the context of the digestive system, it may mean inflated, unsettled (Hipp. Aph. 4.73 528 L., 5.64 556 L.).\n\nIdiomatically, the expression τὰ μετέωρα refers to things in the heaven above, heavenly bodies or to astronomical phenomena.",
}}

Content Guidelines:
- The description should include information derived from text analysis, covering meaning, usage, notable connotations, context, and any contradictions or variations in usage across different authors or texts. If no citations are provided, use your expertise in ancient Greek to provide the best possible analysis.
- Cover meaning, usage, notable connotations, context
- Focus on medical and/or anatomical context. Derive details from analyzing the words around it a context, such as topography features (location), adjectives and qualities, instructions, etc.
- Note any contradictions or variations in usage
- If citations are provided:
  * Use the references to support your analysis, and cite them in the description when they prove a claim you make. 
  * When citing, do so in the abbreviated form accustomed in classical ancient greek corpus studies.
  * Use the full citation in the citations_used section.
- If no citations are provided, use your expertise in ancient Greek, and include a disclaimer in the text.
- Do not make up citations or use external resources. Do not cite or refer to specific corpus texts that aren't in the citations in prompt.
- Only use provided citations to support your analysis


    
Remember: All text must be properly escaped JSON. No raw line breaks or quotes.
"""
