"""
Service layer for LLM operations.
Handles both term analysis and SQL query generation for complex data retrieval.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Type, Union, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.core.config import settings
from app.services.llm.base import BaseLLMClient, LLMResponse
from app.services.llm.bedrock import BedrockClient

class LLMService:
    """Service for managing LLM operations."""
    
    # Map of provider names to their client implementations
    PROVIDERS: Dict[str, Type[BaseLLMClient]] = {
        "bedrock": BedrockClient,
        # Add other providers as they're implemented
        # "openai": OpenAIClient,
        # "local": LocalLLMClient,
    }
    
    # Template for term analysis
    ANALYSIS_TEMPLATE = """You are an expert in ancient medical texts analysis.
        
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
    QUERY_TEMPLATE = """You are an AI assistant that generates SQL queries for a PostgreSQL database. 
The database contains ancient texts with the following schema:

text_lines:
- id: UUID
- content: TEXT (the actual text content)
- line_number: INTEGER
- division_id: UUID (foreign key to text_divisions)
- categories: TEXT[] (array of categories the line belongs to)
- spacy_tokens: JSON (contains text and tokens array, stored as a JSON string)

text_divisions:
- id: UUID
- text_id: UUID (foreign key to texts)
- author_id_field: TEXT (e.g., [0086])
- work_number_field: TEXT (e.g., [055])
- epithet_field: TEXT (optional, e.g., [Divis])
- fragment_field: TEXT (optional)
- volume: TEXT (optional)
- chapter: TEXT (optional)
- line: TEXT (optional)
- section: TEXT (optional, e.g., 847a)
- is_title: BOOLEAN
- title_number: TEXT (optional)
- title_text: TEXT (optional)

texts:
- id: UUID
- title: TEXT
- author_id: UUID (foreign key to authors)
- reference_code: TEXT (optional)
- text_metadata: JSON (optional)

authors:
- id: UUID
- name: TEXT
- normalized_name: TEXT
- language_code: TEXT
- reference_code: TEXT

The spacy_tokens field is a JSON string with this structure:
{{
    "text": "full text content",
    "tokens": [
        {{
            "text": "word text",
            "lemma": "word lemma",
            "pos": "part of speech",
            "tag": "detailed tag",
            "dep": "dependency",
            "morph": "morphology",
            "category": "category if any"
        }},
        ...more tokens...
    ]
}}

Important notes:
1. For searching in spacy_tokens JSON string, use CAST(spacy_tokens AS TEXT) ILIKE '%pattern%'
2. Use array operators (@>) for searching in text_lines.categories
3. Use proper text search functions (to_tsquery, to_tsvector) for text search
4. Include JOINs with text_divisions and texts tables when needed
5. For lemma searches, use: CAST(spacy_tokens AS TEXT) ILIKE '%"lemma":"desired_lemma"%'
6. For category searches, use: categories @> ARRAY['category_name']
7. For citation searches, combine author_id_field, work_number_field, etc.

Task: Generate a SQL query that answers this question: {question}

Only output the SQL query, no explanations.
"""

    # Template for specialized lemma search
    LEMMA_QUERY_TEMPLATE = """Generate a SQL query to find all occurrences of the lemma '{lemma}' 
in the text_lines table, including surrounding context (previous and next lines where available).
Include citation information from text_divisions and texts tables.

Use this schema:
- text_lines (id, content, line_number, division_id, categories, spacy_tokens)
- text_divisions (id, text_id, author_id_field, work_number_field, etc.)
- texts (id, title, author_id)
- authors (id, name, reference_code)

The spacy_tokens field is a JSON string containing tokens array. Search for lemma using:
CAST(spacy_tokens AS TEXT) ILIKE '%"lemma":"{lemma}"%'

The query should:
1. Find lines where the lemma appears in the tokens array
2. Include the previous and next lines for context using window functions
3. Include citation information (author_id_field, work_number_field, etc.)
4. Include the text title and author name
5. Order by text_id and line_number

Only output the SQL query, no explanations.
"""

    # Template for category search
    CATEGORY_QUERY_TEMPLATE = """Generate a SQL query to find all text lines in the category '{category}'.
Include citation information and group by text/division.

Use this schema:
- text_lines (id, content, line_number, division_id, categories, spacy_tokens)
- text_divisions (id, text_id, author_id_field, work_number_field, etc.)
- texts (id, title, author_id)
- authors (id, name, reference_code)

The query should:
1. Find lines where '{category}' is in the categories array using @>
2. Include citation information from text_divisions
3. Include text title and author name
4. Group results by text and division
5. Order by text title and division order

Only output the SQL query, no explanations.
"""

    # Template for lexical value analysis
    LEXICAL_VALUE_TEMPLATE = """
    You are an AI assistant specializing in ancient Greek lexicography and philology. You will build a lexcial value based on validatd texts analysis on a PhD level. Analyze the following word or lemma and its usage in the given citations.
    
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
    Ensure your response is a valid JSON object.
    Properly escape all special characters (e.g., quotes, backslashes) to avoid JSON formatting errors.
    Ensure no truncation occurs.
    Double-check that your JSON is well-formed and escaped correctly according to the JSON specification.
    
    Example JSON Format:

    {{
    "lemma": "{word}",
    "translation": "Your translation here",
    "short_description": "Your short description here",
    "long_description": "Your long description here, ensuring that all special characters are properly escaped.",
    "related_terms": ["term1", "term2", "term3"],
    "citations_used": ["Citation 1", "Citation 2", "Citation 3"],
    }}

    Detailed Long Description:
    The description should include information derived from text analysis, covering meaning, usage, notable connotations, context, and any contradictions or variations in usage across different authors or texts. If no citations are provided, use your expertise in ancient Greek to provide the best possible analysis.

    If citations are provided, make sure to:
    * Reference them in the text to support your claims.
    * Cite them in the accustomed abbreviations. use the full citation in the citations_used section.
    * Make sure to close citations_used list with the brackets.
    
    References
    If citations are provided, you must use them in your analysis. Do not make up citations, don't use extrenal resources, only use what you are given by the user. Use the referencs to support your analysis, and cite them in the description when they prove a claim you make. When citing, do so in the accustomed abbreviations. Provide the full citations you used in the citations_used section. If no citations are provided, use your knowledge of ancient Greek to provide the best possible analysis.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the LLM service."""
        self.session = session
        provider = settings.llm.PROVIDER
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        self.client = self.PROVIDERS[provider]()
        
    async def analyze_term(
        self,
        term: str,
        contexts: list[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Analyze a term using its contexts."""
        context_str = "\n\n".join(
            f"Context {i+1}:\n"
            f"Text: {ctx['text']}\n"
            f"Author: {ctx.get('author', 'Unknown')}\n"
            f"Reference: {ctx.get('reference', 'N/A')}"
            for i, ctx in enumerate(contexts)
        )
        
        prompt = self.ANALYSIS_TEMPLATE.format(
            term=term,
            context_str=context_str
        )
        
        if stream:
            return self.client.stream_generate(
                prompt=prompt,
                max_tokens=max_tokens
            )
        
        return await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )

    async def create_lexical_value(
        self,
        word: str,
        citations: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Generate a lexical value analysis for a word/lemma."""
        # Format citations into a string
        citations_text = "\n\n".join(
            f"Citation {i+1}:\n{ctx.get('text', '')}\n"
            f"Reference: {ctx.get('citation', 'N/A')}"
            for i, ctx in enumerate(citations)
        )
        
        # Format the prompt
        prompt = self.LEXICAL_VALUE_TEMPLATE.format(
            word=word,
            citations=citations_text
        )
        
        # Get response from LLM
        if stream:
            return self.client.stream_generate(
                prompt=prompt,
                max_tokens=max_tokens
            )
        
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        # Parse the JSON response
        try:
            result = json.loads(response.text.strip())
            
            # Validate required fields
            required_fields = ['lemma', 'translation', 'short_description', 
                             'long_description', 'related_terms', 'citations_used']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")

    async def generate_and_execute_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate and execute a SQL query based on a natural language question."""
        response = await self.generate_query(question, max_tokens)
        sql_query = response.text.strip()

        try:
            result = await self.session.execute(text(sql_query))
            rows = result.mappings().all()
            return sql_query, [dict(row) for row in rows]
        except Exception as e:
            raise ValueError(f"Error executing SQL query: {str(e)}")

    async def generate_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate a SQL query based on a natural language question."""
        prompt = self.QUERY_TEMPLATE.format(question=question)
        return await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
    
    async def get_token_count(self, text: str) -> int:
        """Get the token count for a text."""
        return await self.client.count_tokens(text)
    
    async def check_context_length(self, prompt: str) -> bool:
        """Check if a prompt is within the context length limit."""
        token_count = await self.get_token_count(prompt)
        return token_count <= settings.llm.MAX_CONTEXT_LENGTH
