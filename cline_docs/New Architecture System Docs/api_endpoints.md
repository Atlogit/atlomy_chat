# API Endpoints Documentation

## Corpus and Citation Endpoints

### Search Texts
```http
POST /api/v1/corpus/search
```

Request:
```typescript
interface TextSearchRequest {
  query: string;
  search_lemma?: boolean;
  categories?: string[];
}
```

Response:
```typescript
interface SearchResponse {
  results: Citation[];
  results_id: string;
  total_results: number;
}

interface Citation {
  sentence: {
    id: string;
    text: string;
    prev_sentence?: string;
    next_sentence?: string;
    tokens?: any[];
  };
  citation: string;
  context: {
    line_id: string;
    line_text: string;
    line_numbers: number[];
  };
  location: {
    volume?: string;
    chapter?: string;
    section?: string;
    book?: string;
    page?: string;
    fragment?: string;
    line?: string;
  };
  source: {
    author: string;
    work: string;
    author_id?: string;
    work_id?: string;
  };
}
```

### Get Results Page
```http
POST /api/v1/corpus/get-results-page
```

Request:
```typescript
interface PaginationRequest {
  results_id: string;
  page: number;
  page_size: number;
}
```

Response:
```typescript
interface PaginatedResponse {
  results: Citation[];
  page: number;
  page_size: number;
  total_results: number;
}
```

### Search by Category
```http
GET /api/v1/corpus/category/{category}
```

Response: Same as Search Response

### Get Text by ID
```http
GET /api/v1/corpus/text/{text_id}
```

Response:
```typescript
interface TextResponse {
  id: string;
  title: string;
  work_name?: string;
  author?: string;
  reference_code?: string;
  metadata?: Record<string, any>;
  divisions?: TextDivision[];
}

interface TextDivision {
  id: string;
  author_name?: string;
  work_name?: string;
  volume?: string;
  chapter?: string;
  section?: string;
  is_title: boolean;
  title_number?: string;
  title_text?: string;
  metadata?: Record<string, any>;
  lines?: TextLine[];
}

interface TextLine {
  line_number: number;
  content: string;
  categories?: string[];
}
```

## LLM Query Endpoints

### Generate Query
```http
POST /api/v1/llm/generate-query
```

Request:
```typescript
interface QueryGenerationRequest {
  question: string;
  max_tokens?: number;
}
```

Response:
```typescript
interface QueryResponse {
  sql: string;
  results: Citation[];
  results_id: string;
  total_results: number;
  usage: Record<string, number>;
  model: string;
  raw_response?: any;
  error?: string;
}
```

### Get Results Page
```http
POST /api/v1/llm/get-results-page
```

Request:
```typescript
interface PaginationParams {
  results_id: string;
  page: number;
  page_size: number;
}
```

Response: Same as PaginatedResponse

## Cache Management

### Clear Cache
```http
POST /api/v1/corpus/cache/clear
```

Response:
```typescript
interface CacheResponse {
  status: string;
}
```

## Error Handling

All endpoints follow a consistent error response format:

```typescript
interface ErrorResponse {
  detail: string | {
    message: string;
    error_type: string;
    [key: string]: any;
  };
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error

## Pagination

- Results are stored in Redis chunks (1000 items per chunk)
- Each search generates a unique results_id
- Use results_id to fetch additional pages
- Page size is configurable (default: 100)
- Total results count provided in initial response

## Caching Strategy

- Search results cached in Redis
- Cache key format: `{prefix}:{results_id}:chunk:{n}`
- Metadata stored separately: `{prefix}:{results_id}:meta`
- Default TTL: 1 hour (configurable)
- Automatic cache invalidation on updates

## Rate Limiting

- Default: 100 requests per minute per IP
- LLM endpoints: 10 requests per minute per IP
- Cache operations: 5 requests per minute per IP

## Authentication

Currently using basic API key authentication:
- Include API key in Authorization header
- Format: `Authorization: Bearer {api_key}`
- Required for all write operations and cache management
