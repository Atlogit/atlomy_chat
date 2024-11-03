export interface TextLine {
  line_number: number;
  content: string;
  categories?: string[];
  spacy_tokens?: Record<string, any>;
}

export interface TextDivision {
  id: string;
  author_name?: string;
  work_name?: string;
  volume?: string;
  chapter?: string;
  section?: string;
  is_title?: boolean;
  title_text?: string;
  metadata?: Record<string, any>;
  division_metadata?: Record<string, any>;
  lines?: TextLine[];
}

export interface Text {
  id: string;
  title: string;
  author?: string;
  work_name?: string;
  reference_code?: string;
  text_content?: string;
  metadata?: Record<string, any>;
  divisions?: TextDivision[];
}
