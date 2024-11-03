import { UUID } from './types';
import { CitationObject } from './citation';

export interface LemmaAnalysis {
  id: UUID;
  analysis_text: string;
  analysis_data?: Record<string, any>;
  citationstest?: Record<string, any>;
  created_by: string;
}

export interface LexicalValue {
  id: UUID;
  lemma: string;
  language_code?: string;
  categories: string[];
  translations?: Record<string, any>;
  translation?: string;
  short_description?: string;
  long_description?: string;
  related_terms?: string[];
  citations_used: string[];  // LLM's citations as simple strings
  references: {              // System-generated citations with full context
    citations: CitationObject[];
  };
  analyses: LemmaAnalysis[];
  created_at: string;
  updated_at: string;
  version: string;
}

export interface LemmaCreate {
  lemma: string;
  searchLemma?: boolean;
  language_code?: string;
  categories?: string[];
  translations?: Record<string, any>;
  analyze?: boolean;
}

export interface LemmaBatchCreate {
  lemmas: LemmaCreate[];
}

export interface BatchCreateResponse {
  successful: LexicalValue[];
  failed: Array<{
    lemma: string;
    error: string;
  }>;
  total: number;
}

export interface CreateResponse {
  task_id: UUID;
  message: string;
}

export interface TaskStatus {
  status: 'in_progress' | 'completed' | 'error';
  message: string;
  entry?: LexicalValue;
  action?: 'create' | 'update';
}

export interface DeleteTriggerResponse {
  trigger_id: string;
  message: string;
  entry: LexicalValue;
}
