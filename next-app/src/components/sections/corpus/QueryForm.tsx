'use client'

import { useState, useCallback } from 'react'
import { Button } from '../../ui/Button'
import { PaginatedResults } from '../../ui/PaginatedResults'
import { ResultsDisplay } from '../../ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, QueryGenerationRequest, PreciseQueryRequest, QueryResponse, Citation } from '../../../utils/api'

type QueryType = 'natural' | 'lemma_search' | 'category_search' | 'citation_search';

/**
 * QueryForm Component
 * 
 * This component provides a form for generating SQL queries using either natural language
 * questions or precise query parameters.
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
  const { data, error, isLoading, execute } = useApi<QueryResponse>()
  
  /**
   * Handles the form submission to generate a SQL query.
   * 
   * @async
   * @function
   */
  const handleSubmit = useCallback(async () => {
    if (isLoading) return; // Prevent multiple submissions while loading

    try {
      if (queryType === 'natural') {
        if (!question.trim()) return
        
        const request: QueryGenerationRequest = {
          question: question.trim(),
          max_tokens: 1000
        }
        
        await execute(API.llm.generateQuery, {
          method: 'POST',
          body: JSON.stringify(request)
        })
      } else {
        // Handle precise query generation
        const request: PreciseQueryRequest = {
          query_type: queryType,
          parameters: {},
          max_tokens: 1000
        }

        switch (queryType) {
          case 'lemma_search':
            if (!lemma.trim()) return
            request.parameters.lemma = lemma.trim()
            break
          case 'category_search':
            if (!category.trim()) return
            request.parameters.category = category.trim()
            break
          case 'citation_search':
            if (!authorId.trim() || !workNumber.trim()) return
            request.parameters.author_id = authorId.trim()
            request.parameters.work_number = workNumber.trim()
            break
        }

        await execute(API.llm.generatePreciseQuery, {
          method: 'POST',
          body: JSON.stringify(request)
        })
      }
    } catch (err) {
      console.error('Error in handleSubmit:', err)
    }
  }, [queryType, question, lemma, category, authorId, workNumber, execute, isLoading])

  const renderQueryInputs = () => {
    switch (queryType) {
      case 'natural':
        return (
          <textarea
            className="textarea textarea-bordered w-full h-24"
            placeholder="e.g., Find all sentences containing words from the 'anatomy' category that are also nouns"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            spellCheck="false"
            data-ms-editor="true"
            disabled={isLoading}
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
            disabled={isLoading}
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
            disabled={isLoading}
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
              disabled={isLoading}
            />
            <input
              type="text"
              className="input input-bordered w-full"
              placeholder="Work Number (e.g., 055)"
              value={workNumber}
              onChange={(e) => setWorkNumber(e.target.value)}
              disabled={isLoading}
            />
          </div>
        )
    }
  }

  const isSubmitDisabled = () => {
    switch (queryType) {
      case 'natural':
        return !question.trim() || isLoading
      case 'lemma_search':
        return !lemma.trim() || isLoading
      case 'category_search':
        return !category.trim() || isLoading
      case 'citation_search':
        return !authorId.trim() || !workNumber.trim() || isLoading
      default:
        return true
    }
  }

  return (
    <div className="form-control gap-4">
      <div>
        <label className="label">
          <span className="label-text">Query Type</span>
        </label>
        <select
          className="select select-bordered w-full"
          value={queryType}
          onChange={(e) => setQueryType(e.target.value as QueryType)}
          disabled={isLoading}
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
            {queryType === 'natural' ? 'Ask a question about the corpus data' : 'Enter search parameters'}
          </span>
        </label>
        {renderQueryInputs()}
      </div>

      <Button
        onClick={handleSubmit}
        isLoading={isLoading}
        disabled={isSubmitDisabled()}
      >
        Generate SQL Query
      </Button>

      {error && (
        <div className="alert alert-error">
          <p>{error.message}</p>
          {error.detail && <p className="text-sm mt-1">{error.detail}</p>}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="ml-4">Generating query and fetching results...</p>
        </div>
      )}

      {data?.sql && (
        <ResultsDisplay
          title="Generated SQL Query"
          content={data.sql}
          className="p-4 bg-base-200 rounded-lg"
        />
      )}

      {data?.results && (
        <PaginatedResults
          title="Query Results"
          results={data.results}
          pageSize={10}
          className="mt-4"
          isLoading={isLoading}
        />
      )}

      {/* Debug output */}
      {data && (
        <div className="mt-4 p-4 bg-base-200 rounded-lg">
          <h4 className="font-bold mb-2">Debug Info:</h4>
          <pre className="whitespace-pre-wrap text-sm">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
