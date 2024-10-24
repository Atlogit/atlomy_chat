'use client'

import { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API } from '../../../utils/api'

interface LLMResponse {
  result?: any[];
  answer?: string;
  stage?: string;
}

const RESULTS_PER_PAGE = 10;

/**
 * LLMSection Component
 * 
 * This component represents the LLM (Language Model) Assistant section of the application.
 * It provides an interface for users to input queries and receive responses from the LLM.
 * 
 * @component
 */
export function LLMSection() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')
  const [fullResult, setFullResult] = useState<any[] | null>(null)
  const [processingStage, setProcessingStage] = useState<string | null>(null)
  const [isHtmlResponse, setIsHtmlResponse] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const { data, error, isLoading, execute } = useApi<LLMResponse>()

  useEffect(() => {
    if (data) {
      handleApiResponse(data)
    }
  }, [data])

  useEffect(() => {
    if (fullResult) {
      displayPaginatedResults();
    }
  }, [fullResult, currentPage]);

  /**
   * Handles the submission of the query to the LLM API.
   * 
   * @async
   * @function
   */
  const handleSubmit = async () => {
    if (!query.trim()) return

    setProcessingStage('Initializing query...')
    setIsHtmlResponse(false)
    setCurrentPage(1)

    await execute(API.llm.query, {
      method: 'POST',
      body: JSON.stringify({ query }),
    })

    // Clear query after submission
    setQuery('')
  }

  const handleApiResponse = (result: LLMResponse) => {
    console.log('API response:', result)

    if (result && typeof result === 'object') {
      if ('answer' in result && typeof result.answer === 'string') {
        setResponse(result.answer)
        setFullResult(null)
      } else if ('result' in result && Array.isArray(result.result)) {
        const summary = `The query returned ${result.result.length} results.`
        setResponse(summary)
        setFullResult(result.result)
      } else {
        console.warn('Unexpected API response format:', result)
        setResponse('The API response was in an unexpected format. Please try again.')
        setFullResult(null)
      }
    } else {
      console.error('Unexpected API response format:', result)
      setResponse('An error occurred while processing your query. Please try again.')
      setFullResult(null)
    }

    setProcessingStage(null)
  }

  const displayPaginatedResults = () => {
    if (fullResult) {
      const startIndex = (currentPage - 1) * RESULTS_PER_PAGE;
      const endIndex = startIndex + RESULTS_PER_PAGE;
      const paginatedResults = fullResult.slice(startIndex, endIndex);

      const formattedResult = paginatedResults.map((item, index) => (
        `<div class="mb-4 p-4 bg-base-200 rounded shadow">
          <strong class="text-lg">${startIndex + index + 1}.</strong>
          <p class="mt-2">${item}</p>
        </div>`
      )).join('')

      const paginationInfo = `<div class="mt-4 text-center">
        Showing results ${startIndex + 1} - ${Math.min(endIndex, fullResult.length)} of ${fullResult.length}
      </div>`

      setResponse(formattedResult + paginationInfo)
      setIsHtmlResponse(true)
    }
  }

  const handleViewFullResult = () => {
    setCurrentPage(1)
    displayPaginatedResults()
  }

  const handleNextPage = () => {
    if (fullResult && currentPage < Math.ceil(fullResult.length / RESULTS_PER_PAGE)) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">LLM Assistant</h2>
        <div className="form-control">
          <textarea
            className="textarea textarea-bordered h-32 w-full"
            placeholder="Ask a question about the texts..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="flex gap-2 mt-4">
            <Button
              onClick={handleSubmit}
              isLoading={isLoading}
              disabled={!query.trim()}
              className="flex-1"
            >
              Ask Question
            </Button>
            {fullResult && (
              <Button onClick={handleViewFullResult} variant="outline">
                View Full Result
              </Button>
            )}
          </div>
        </div>
        {(isLoading || processingStage) && (
          <div className="mt-4 flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mr-2"></div>
            <span>{processingStage || 'Processing...'}</span>
          </div>
        )}
        <ResultsDisplay
          content={error ? null : response}
          error={error ? error.message : null}
          isHtml={isHtmlResponse}
        />
        {fullResult && fullResult.length > RESULTS_PER_PAGE && (
          <div className="flex justify-center gap-2 mt-4">
            <Button onClick={handlePrevPage} disabled={currentPage === 1} variant="outline">
              Previous
            </Button>
            <Button onClick={handleNextPage} disabled={currentPage >= Math.ceil(fullResult.length / RESULTS_PER_PAGE)} variant="outline">
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
