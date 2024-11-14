import { CitationObject } from './citation';

/**
 * Request model for text search operations
 */
export interface TextSearchRequest {
  query: string;
  search_lemma?: boolean;
  categories?: string[];
}

/**
 * Request model for paginated results
 */
export interface PaginationRequest {
  results_id: string;
  page: number;
  page_size: number;
}

/**
 * Response model for search operations
 * Contains both results and pagination metadata
 */
export interface SearchResponse {
  results: CitationObject[];
  results_id: string;
  total_results: number;
}

/**
 * Response model for paginated results
 */
export interface PaginatedResponse {
  results: CitationObject[];
  page: number;
  page_size: number;
  total_results: number;
}

/**
 * Response model for natural language query operations
 */
export interface QueryResponse {
  sql: string;
  results: CitationObject[];
  results_id: string;
  total_results: number;
  error?: string;
}

export type SearchResult = CitationObject;
