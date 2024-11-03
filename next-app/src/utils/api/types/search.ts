export interface TextSearchRequest {
  query: string;
  search_lemma?: boolean;
  categories?: string[];
}

export interface SearchResult {
  text_id: string;
  sentence_id: string;
  sentence_text: string;
  sentence_tokens?: Record<string, any>;
  line_id: string;
  line_text: string;
  line_numbers: number[];
  min_line_number: number;
  division_id: string;
  author_name?: string;
  work_name?: string;
  volume?: string;
  chapter?: string;
  section?: string;
  prev_sentence?: string;
  next_sentence?: string;
  categories?: string[];
  spacy_data?: Record<string, any>;
}
