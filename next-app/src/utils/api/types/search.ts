import { CitationObject } from './citation';

export interface TextSearchRequest {
  query: string;
  search_lemma?: boolean;
  categories?: string[];
}

export type SearchResult = CitationObject;
