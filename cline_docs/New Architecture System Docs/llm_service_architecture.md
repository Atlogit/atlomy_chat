# LLM Service Architecture

## Overview

The LLM service has been restructured into focused, modular components to improve maintainability and separation of concerns. Each component handles a specific aspect of LLM operations while maintaining a clean interface through the main LLM service.

## Component Structure

### 1. Base Service (base_service.py)
- Core LLM functionality shared across all services
- Provider management and initialization
- Token counting and context length checking
- Error handling and logging
- Common utilities

```python
class BaseLLMService:
    def __init__(self, session: AsyncSession):
        # Initialize provider
        # Set up logging
        # Configure error handling

    async def get_token_count(self, text: str) -> int:
        # Count tokens in text

    async def check_context_length(self, prompt: str) -> bool:
        # Check if prompt is within context limits
```

### 2. Lexical Service (lexical_service.py)
- Specialized for lexical value generation
- JSON response handling and validation
- Citation formatting
- Comprehensive error handling for lexical operations

```python
class LexicalLLMService(BaseLLMService):
    async def create_lexical_value(
        self,
        word: str,
        citations: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        # Generate lexical value analysis
```

### 3. Query Service (query_service.py)
- SQL query generation and execution
- Support for different query types:
  - Natural language queries
  - Lemma searches
  - Category searches
- Result formatting and citation handling

```python
class QueryLLMService(BaseLLMService):
    async def generate_and_execute_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        # Generate and execute SQL query
```

### 4. Analysis Service (analysis_service.py)
- Text analysis functionality
- Context handling
- Term analysis with citations

```python
class AnalysisLLMService(BaseLLMService):
    async def analyze_term(
        self,
        term: str,
        contexts: List[Dict[str, Any]],
        max_tokens: Optional[int] = None
    ) -> str:
        # Generate term analysis
```

### 5. Main Service (llm_service.py)
- Coordinates between specialized services
- Maintains clean interface for API layer
- Delegates operations to appropriate services

```python
class LLMService:
    def __init__(self, session: AsyncSession):
        self.lexical_service = LexicalLLMService(session)
        self.query_service = QueryLLMService(session)
        self.analysis_service = AnalysisLLMService(session)

    # Methods delegate to specialized services while maintaining
    # the same interface for API compatibility
```

## Prompt Templates

Prompt templates are organized into separate files for better maintainability:

1. lexical_prompts.py
   - Templates for lexical value generation
   - Structured JSON output format

2. analysis_prompts.py
   - Templates for text analysis
   - Scholarly analysis format

3. prompts.py
   - SQL query generation templates
   - Database schema and query patterns

## API Integration

The API layer interacts only with the main LLMService class, which maintains backward compatibility while delegating to specialized services internally. This design allows for:

- Clean separation of concerns
- Easy maintenance and updates
- No changes needed in API layer
- Consistent error handling

## Error Handling

Each service inherits from BaseLLMService and implements:
- Specific error types
- Detailed error messages
- Proper error propagation
- Comprehensive logging

## Usage Example

```python
# API layer remains unchanged
@router.post("/generate-query")
async def generate_query(
    data: QueryGenerationRequest,
    llm_service: LLMServiceDep
) -> Dict:
    # LLMService delegates to QueryLLMService internally
    sql_query, results = await llm_service.generate_and_execute_query(
        question=data.question,
        max_tokens=data.max_tokens
    )
    # Process results...
```

## Benefits

1. **Maintainability**
   - Each service has a single responsibility
   - Changes can be made without affecting other components
   - Easier to test and debug

2. **Scalability**
   - New services can be added easily
   - Each service can be optimized independently
   - Clear separation of concerns

3. **Reliability**
   - Consistent error handling
   - Better logging and monitoring
   - Easier to implement retries and fallbacks

4. **Flexibility**
   - Easy to add new LLM providers
   - Simple to extend functionality
   - Clean interface for future changes
