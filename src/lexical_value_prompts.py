BATCH_GENERATION_PROMPT = """
You are an expert in ancient Greek terminology and philology, specializing in medical terminology with deep knowledge of Hippocratic and Galenic medicine. Your task is to generate comprehensive lexical entries for Greek terms found in the following texts and their associated citations.

Texts:
{texts}

Citations:
{citations}

For each significant medical term you identify across all texts, create a lexical entry with the following structure:
1. Lemma: The basic form of the term in ancient Greek (transliterated if necessary)
2. Translation: Precise English translation
3. Short Description: A concise explanation (2-3 sentences) focusing on the term's primary medical significance
4. Long Description: A detailed explanation including:
   - Historical context and origin of the term
   - Usage in the referenced texts, based on the citations, and with context of Hippocratic and Galenic medicine
   - Evolution of the term's meaning over time
   - Analysis of the term's significance in ancient medical theory
   - How the term relates to the four humors theory, if applicable
   - Any modern medical correlates or how understanding has changed
5. Related Terms: Other medical terms that are closely related, with brief explanations of their relationships
6. References: Relevant citations or mentions in ancient texts, including specific passages and their significance

Consider different types of medical terms:
- Anatomical terms: Describe the ancient understanding of the body part and its function
- Disease names: Explain the ancient conception of the disease, its causes, and treatments
- Therapeutic concepts: Discuss the theoretical basis and practical application
- Physiological processes: Relate to ancient theories of body function and health

Present your findings in a JSON format, with each lexical entry as an object in a list. Ensure that your entries are comprehensive, historically accurate, and reflect the nuances of ancient Greek medical thought across all provided texts.
JSON structure:
{{
    "lemma": "{word}",
    "translation": "Your translation here",
    "short_description": "Your short description here",
    "long_description": "Your long description here",
    "related_terms": ["term1", "term2", "term3"],
    "references": ["Citation 1", "Citation 2", "Citation 3"]
}}


    make sure your response is formatted for JSON.
"""

SUGGEST_UPDATES_PROMPT = """
You are an expert in ancient Greek medical terminology, with deep knowledge of Hippocratic and Galenic medicine. Your task is to suggest updates to an existing lexical entry based on new information. Consider the historical context, the evolution of medical thought, and the significance of the term in ancient Greek medicine.

Existing Entry:
{existing_entry}

New Text:
{new_text}

Please suggest updates to the following fields if necessary:
1. Translation: Ensure the most accurate and nuanced English translation
2. Short Description: Refine the concise explanation based on new insights
3. Long Description: Expand or modify the detailed explanation, considering:
   - Any new historical context or origin information
   - Updated understanding of its usage in the referenced texts and citations.
   - New insights into the term's evolution or significance
   - How it relates to ancient medical theories (e.g., four humors, if applicable)
   - Any newly discovered modern medical correlates
4. Related Terms: Add or modify related terms based on new connections or insights
5. References: Include any new relevant citations or mentions in ancient texts

Present your suggestions in a JSON format, including only the fields that need updating. Provide a brief explanation for each suggested change. Example structure:

{{
    "lemma": "{word}",
    "translation": "Your translation here",
    "short_description": "Your short description here",
    "long_description": "Your long description here",
    "related_terms": ["term1", "term2", "term3"],
    "references": ["Citation 1", "Citation 2", "Citation 3"]
}}

Ensure that your suggestions are well-justified, historically accurate, and enhance the overall quality and depth of the lexical entry.
"""
