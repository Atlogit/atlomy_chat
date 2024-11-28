// Explicitly import and re-export types to resolve naming conflicts
export type { 
  UUID, 
  ApiError, 
  ProcessingStatus, 
  SearchResult as GlobalSearchResult, 
  NoResultsMetadata as GlobalNoResultsMetadata 
} from './api/types/types';

// Explicitly import and re-export search types
export type { 
  NoResultsMetadata as SearchNoResultsMetadata,
  TextSearchRequest,
  QueryGenerationRequest,
  SearchResponse,
  PaginatedResponse,
  QueryResponse,
  SearchResult
} from './api/types/search';

// Explicitly import and re-export other type files
export * from './api/types/text';
export * from './api/types/llm';
export * from './api/types/citation';
export * from './api/types/lexical';

export { fetchApi } from './api/fetch';
export { API } from './api/endpoints';
