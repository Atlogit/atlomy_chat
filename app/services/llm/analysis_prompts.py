"""
LLM prompt templates for text analysis tasks.
"""

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
