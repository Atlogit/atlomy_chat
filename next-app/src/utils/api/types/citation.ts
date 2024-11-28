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
    epistle?: string;
    fragment?: string;
    volume?: string;
    book?: string;
    chapter?: string;
    section?: string;
    page?: string;
    line?: string;
  };
  source: {
    author: string;
    work: string;
    author_id?: string;
    work_id?: string;
  };
}

export type Citation = CitationObject | string;
