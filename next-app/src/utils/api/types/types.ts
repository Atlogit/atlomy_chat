export type UUID = string;

export interface NoResultsMetadata {
  original_question: string;
  generated_query: string;
  search_description: string;
  search_criteria: Record<string, string>;
}

export interface ApiError {
  message: string;
  status?: number;
  detail?: {
    message: string;
    error_type?: 
      | 'query_timeout'
      | 'database_error'
      | 'citation_format_error'
      | 'unexpected_error'
      | 'empty_response'
      | 'parse_error'
      | 'js_error'
      | 'unknown_error';
    sql_query?: string;
    row_count?: number;
    raw_error?: string;  
  } | string;
}

export interface ProcessingStatus {
  results_id: UUID;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processed_citations: number;
  total_citations: number;
  error?: ApiError;
}

export interface SearchResult {
  sentence?: {
    id: string;
    text: string;
    prev_sentence?: string;
    next_sentence?: string;
    tokens?: Record<string, any>;
  };
  citation?: string;
  context?: {
    line_id?: string;
    line_text?: string;
    line_numbers?: number[];
  };
  location?: {
    // Location fields
    epistle?: string;
    fragment?: string;
    volume?: string;
    book?: string;
    chapter?: string;
    section?: string;
    page?: string;
    line?: string;
  };
  source?: {
    author: string;
    work: string;
    author_id?: string;
    work_id?: string;
    work_abbreviation?: string;
    author_abbreviation?: string;
  };
}

export interface QueryResponse {
  sql: string;
  results: SearchResult[];
  results_id: string;
  total_results: number;
  usage: Record<string, number>;
  model: string;
  raw_response?: Record<string, any>;
  error?: string;
  no_results_metadata?: NoResultsMetadata;
}

export interface SearchResponse {
  results: SearchResult[];
  results_id: string;
  total_results: number;
  no_results_metadata?: NoResultsMetadata;
}
