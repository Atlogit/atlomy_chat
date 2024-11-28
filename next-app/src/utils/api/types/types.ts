export type UUID = string;

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
    tokens?: string[];
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
