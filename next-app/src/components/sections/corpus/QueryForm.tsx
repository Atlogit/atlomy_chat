'use client'

import { useState, useCallback } from 'react'
import { Button } from '../../ui/Button'
import { PaginatedResults } from '../../ui/PaginatedResults'
import { ResultsDisplay } from '../../ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { 
  API, 
  SearchResult, 
  TextSearchRequest, 
  QueryGenerationRequest,
  QueryResponse,
  PaginatedResponse,
  SearchResponse 
} from '../../../utils/api'

type QueryType = 'natural' | 'lemma_search' | 'category_search' | 'citation_search';

/**
 * QueryForm Component
 * 
 * This component provides a form for searching the corpus using different search types.
 * For natural language queries, it uses LLM to generate appropriate search parameters.
 *
 * @component
 */
export function QueryForm() {
  const [queryType, setQueryType] = useState<QueryType>('natural')
  const [question, setQuestion] = useState('')
  const [lemma, setLemma] = useState('')
  const [category, setCategory] = useState('')
  const [authorId, setAuthorId] = useState('')
  const [workNumber, setWorkNumber] = useState('')
  const [generatedQuery, setGeneratedQuery] = useState('')
  const [queryResults, setQueryResults] = useState<SearchResult[]>([])
  const [resultsId, setResultsId] = useState<string>('')
  const [totalResults, setTotalResults] = useState<number>(0)
  const { data: searchResults, error: searchError, isLoading: isSearching, execute: executeSearch } = useApi<SearchResponse>()
  const { data: queryData, error: queryError, isLoading: isGenerating, execute: executeGenerate } = useApi<QueryResponse>()
  const { data: pageData, error: pageError, isLoading: isLoadingPage, execute: executePage } = useApi<PaginatedResponse>()
  
  /**
   * Handles fetching additional pages of results
   */
  const fetchResultsPage = useCallback(async (page: number, pageSize: number) => {
    if (!resultsId || isLoadingPage) return [];

    try {
      const response = await executePage(API.llm.getResultsPage, {
        method: 'POST',
        body: JSON.stringify({
          results_id: resultsId,
          page,
          page_size: pageSize
        })
      });

      if (response?.results) {
        return response.results;
      }
      return [];
    } catch (err) {
      console.error('Error fetching results page:', err);
      return [];
    }
  }, [resultsId, isLoadingPage, executePage]);

  /**
   * Handles the form submission to search the corpus.
   * For natural language queries, first generates a search query using LLM.
   * 
   * @async
   * @function
   */
  const handleSubmit = useCallback(async () => {
    if (isSearching || isGenerating) return; // Prevent multiple submissions while loading

    try {
      switch (queryType) {
        case 'natural':
          if (!question.trim()) return

          // Generate the appropriate search query using LLM
          const request: QueryGenerationRequest = {
            question: question.trim(),
            max_tokens: 1000
          }
          
          const queryResult = await executeGenerate(API.llm.generateQuery, {
            method: 'POST',
            body: JSON.stringify(request)
          })

          if (queryResult?.sql) {
            setGeneratedQuery(queryResult.sql)
            if (queryResult.results) {
              setQueryResults(queryResult.results)
              setResultsId(queryResult.results_id)
              setTotalResults(queryResult.total_results)
            }
          }
          break

        case 'lemma_search':
          if (!lemma.trim()) return
          
          const lemmaRequest: TextSearchRequest = {
            query: lemma.trim(),
            search_lemma: true
          }
          
          const lemmaResult = await executeSearch(API.corpus.search, {
            method: 'POST',
            body: JSON.stringify(lemmaRequest)
          })

          if (lemmaResult) {
            setQueryResults(lemmaResult.results)
            setResultsId(lemmaResult.results_id)
            setTotalResults(lemmaResult.total_results)
          }
          break

        case 'category_search':
          if (!category.trim()) return
          const categoryResult = await executeSearch(API.corpus.category(category.trim()))
          if (categoryResult) {
            setQueryResults(categoryResult.results)
            setResultsId(categoryResult.results_id)
            setTotalResults(categoryResult.total_results)
          }
          break

        case 'citation_search':
          if (!authorId.trim() || !workNumber.trim()) return
          const citationRequest: TextSearchRequest = {
            query: `${authorId.trim()} ${workNumber.trim()}`,
            search_lemma: false
          }
          
          const citationResult = await executeSearch(API.corpus.search, {
            method: 'POST',
            body: JSON.stringify(citationRequest)
          })

          if (citationResult) {
            setQueryResults(citationResult.results)
            setResultsId(citationResult.results_id)
            setTotalResults(citationResult.total_results)
          }
          break
      }
    } catch (err) {
      console.error('Error in handleSubmit:', err)
    }
  }, [queryType, question, lemma, category, authorId, workNumber, executeSearch, executeGenerate, isSearching, isGenerating])

  const renderQueryInputs = () => {
    switch (queryType) {
      case 'natural':
        return (
          <textarea
            className="textarea textarea-bordered w-full h-24"
            placeholder="Ask any question about the corpus (e.g., 'find all sentences with words in the anatomy category' or 'where does Galen talk about nose and water?')"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            spellCheck="false"
            data-ms-editor="true"
            disabled={isSearching || isGenerating}
          />
        )
      case 'lemma_search':
        return (
          <input
            type="text"
            className="input input-bordered w-full"
            placeholder="Enter lemma to search for"
            value={lemma}
            onChange={(e) => setLemma(e.target.value)}
            disabled={isSearching}
          />
        )
      case 'category_search':
        return (
          <input
            type="text"
            className="input input-bordered w-full"
            placeholder="Enter category name"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            disabled={isSearching}
          />
        )
      case 'citation_search':
        return (
          <div className="flex gap-4">
            <input
              type="text"
              className="input input-bordered w-full"
              placeholder="Author ID (e.g., 0086)"
              value={authorId}
              onChange={(e) => setAuthorId(e.target.value)}
              disabled={isSearching}
            />
            <input
              type="text"
              className="input input-bordered w-full"
              placeholder="Work Number (e.g., 055)"
              value={workNumber}
              onChange={(e) => setWorkNumber(e.target.value)}
              disabled={isSearching}
            />
          </div>
        )
    }
  }

  const isSubmitDisabled = () => {
    switch (queryType) {
      case 'natural':
        return !question.trim() || isSearching || isGenerating
      case 'lemma_search':
        return !lemma.trim() || isSearching
      case 'category_search':
        return !category.trim() || isSearching
      case 'citation_search':
        return !authorId.trim() || !workNumber.trim() || isSearching
      default:
        return true
    }
  }

  const renderError = (error: any) => {
    if (!error) return null;

    return (
      <div className="alert alert-error">
        <p className="font-semibold">{error.message}</p>
        {error.detail && (
          <div className="text-sm mt-2">
            {typeof error.detail === 'object' ? (
              <>
                {error.detail.message && <p>{error.detail.message}</p>}
                {error.detail.error_type && (
                  <p className="text-xs mt-1 opacity-75">
                    Error type: {error.detail.error_type}
                  </p>
                )}
                {error.detail.sql_query && (
                  <div className="mt-2">
                    <p className="font-semibold">Generated SQL:</p>
                    <pre className="text-xs mt-1 bg-base-300 p-2 rounded">
                      {error.detail.sql_query}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <p>{error.detail}</p>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="form-control gap-4">
      <div>
        <label className="label">
          <span className="label-text">Search Type</span>
        </label>
        <select
          className="select select-bordered w-full"
          value={queryType}
          onChange={(e) => setQueryType(e.target.value as QueryType)}
          disabled={isSearching || isGenerating}
        >
          <option value="natural">Natural Language Query</option>
          <option value="lemma_search">Lemma Search</option>
          <option value="category_search">Category Search</option>
          <option value="citation_search">Citation Search</option>
        </select>
      </div>

      <div>
        <label className="label">
          <span className="label-text">
            {queryType === 'natural' ? 'Ask any question about the corpus' : 'Enter search parameters'}
          </span>
        </label>
        {renderQueryInputs()}
      </div>

      <Button
        onClick={handleSubmit}
        isLoading={isSearching || isGenerating}
        disabled={isSubmitDisabled()}
      >
        Search
      </Button>

      {(queryError || searchError || pageError) && renderError(queryError || searchError || pageError)}

      {(isSearching || isGenerating || isLoadingPage) && (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="ml-4">
            {isGenerating ? 'Analyzing your question...' : 
             isLoadingPage ? 'Loading more results...' : 'Searching corpus...'}
          </p>
        </div>
      )}

      {generatedQuery && queryType === 'natural' && (
        <ResultsDisplay
          title="Generated Query"
          content={generatedQuery}
          className="p-4 bg-base-200 rounded-lg"
        />
      )}

      {queryType === 'natural' && queryResults.length > 0 && (
        <PaginatedResults
          title={`Search Results (${totalResults} total)`}
          results={queryResults}
          pageSize={10}
          className="mt-4"
          isLoading={isGenerating || isLoadingPage}
          onPageChange={fetchResultsPage}
          totalResults={totalResults}
        />
      )}

      {queryType !== 'natural' && searchResults?.results && searchResults.results.length > 0 && (
        <PaginatedResults
          title={`Search Results (${totalResults} total)`}
          results={searchResults.results}
          pageSize={10}
          className="mt-4"
          isLoading={isSearching}
          onPageChange={fetchResultsPage}
          totalResults={totalResults}
        />
      )}
    </div>
  )
}
