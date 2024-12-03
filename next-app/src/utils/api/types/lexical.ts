import { UUID } from './types';
import { CitationObject } from './citation';

export interface LLMParameters {
  temperature?: number;
  top_p?: number;
  top_k?: number;
  max_length?: number;
  stop_sequences?: string[];
}

export interface Version {
  version: string;
  created_at?: string;
  updated_at?: string;
  model?: string;
  parameters?: LLMParameters;
}

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
  metadata?: {
    llm_config?: {
      model_id?: string;
      temperature?: number;
      top_p?: number;
      top_k?: number;
      max_length?: number;
      stop_sequences?: string[];
    }
  }
}

export interface LemmaCreate {
  lemma: string;
  searchLemma?: boolean;
  language_code?: string;
  categories?: string[];
  translations?: Record<string, any>;
  analyze?: boolean;
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

export interface VersionsResponse {
  versions: Version[];
}
