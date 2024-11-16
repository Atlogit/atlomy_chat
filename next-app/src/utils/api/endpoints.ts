import { UUID } from './types/types';

export const API = {
  llm: {
    analyze: '/api/v1/llm/analyze',
    analyzeStream: '/api/v1/llm/analyze/stream',
    tokenCount: '/api/v1/llm/token-count',
    generateQuery: '/api/v1/llm/generate-query',
    generatePreciseQuery: '/api/v1/llm/generate-precise-query',
    getResultsPage: '/api/v1/llm/get-results-page',
  },
  lexical: {
    create: '/api/v1/lexical/create',
    get: (lemma: string) => `/api/v1/lexical/get/${encodeURIComponent(lemma)}`,
    list: '/api/v1/lexical/list',
    update: '/api/v1/lexical/update',
    delete: (lemma: string) => `/api/v1/lexical/delete/${encodeURIComponent(lemma)}`,
    deleteTrigger: (lemma: string) => `/api/v1/lexical/delete/${encodeURIComponent(lemma)}/trigger`,
    status: (taskId: UUID) => `/api/v1/lexical/status/${encodeURIComponent(taskId)}`,
    versions: (lemma: string) => `/api/v1/lexical/versions/${encodeURIComponent(lemma)}`,
  },
  corpus: {
    list: '/api/v1/corpus/list',
    search: '/api/v1/corpus/search',
    all: '/api/v1/corpus/all',
    text: (id: string) => `/api/v1/corpus/text/${encodeURIComponent(id)}`,
    category: (category: string) => `/api/v1/corpus/category/${encodeURIComponent(category)}`,
    clearCache: '/api/v1/corpus/cache/clear',
  },
};
