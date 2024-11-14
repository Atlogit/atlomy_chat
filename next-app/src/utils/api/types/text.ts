export interface TokenInfo {
  text: string;
  lemma: string;
  pos: string;
  tag: string;
  dep: string;
  morph: string;
  category: string;
  is_stop: boolean;
  is_punct: boolean;
}

export interface SpacyTokens {
  tokens: TokenInfo[];
}

export interface TextLine {
  line_number: number;
  content: string;
  categories?: string[];
  spacy_tokens?: TokenInfo[] | SpacyTokens;  // Can be array or object with tokens array
}

export interface TextDivision {
  id: string;
  author_name?: string;
  work_name?: string;
  volume?: string;
  chapter?: string;
  section?: string;
  is_title: boolean;
  title_text?: string;
  metadata?: Record<string, any>;
  lines?: TextLine[];
}

export interface Text {
  id: string;
  title: string;
  work_name?: string;
  author?: string;
  reference_code?: string;
  metadata?: Record<string, any>;
  divisions?: TextDivision[];
}
