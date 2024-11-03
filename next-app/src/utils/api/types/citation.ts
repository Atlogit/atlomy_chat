export interface CitationObject {
  sentence: {
    id: string;
    text: string;
    prev_sentence?: string;
    next_sentence?: string;
    tokens?: Record<string, any>;
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
  };
  source: {
    author: string;
    work: string;
  };
}

export type Citation = CitationObject | string;
