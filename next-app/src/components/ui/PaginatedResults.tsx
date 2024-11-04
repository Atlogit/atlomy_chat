import { useState, useEffect } from 'react'
import { SearchResult } from '../../utils/api'
import { ResultsDisplay } from './ResultsDisplay'

interface PaginatedResultsProps {
  title?: string
  results: SearchResult[]
  pageSize?: number
  className?: string
  isLoading?: boolean
}

export function PaginatedResults({
  title = 'Results',
  results,
  pageSize = 10,
  className = '',
  isLoading = false,
}: PaginatedResultsProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [paginatedResults, setPaginatedResults] = useState<SearchResult[]>([])
  const totalPages = Math.ceil(results.length / pageSize)

  useEffect(() => {
    if (!results.length) {
      setPaginatedResults([])
      return
    }

    const start = (currentPage - 1) * pageSize
    const end = start + pageSize
    const pageResults = results.slice(start, end)
    setPaginatedResults(pageResults)
  }, [results, currentPage, pageSize])

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        <p className="text-center text-base-content/70">Loading results...</p>
      </div>
    )
  }

  if (!results.length) {
    return (
      <div className={`space-y-4 ${className}`}>
        <p className="text-center text-base-content/70">No results found</p>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between items-center">
        <h3 className="font-bold">{title}</h3>
        <div className="text-sm text-base-content/70">
          Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, results.length)} of {results.length} results
        </div>
      </div>

      <div className="space-y-4">
        {paginatedResults.map((result, index) => (
          <div key={`${result.sentence_id || index}-${index}`} className="p-4 bg-base-200 rounded-lg">
            <div className="mb-2">
              <span className="font-semibold">Source: </span>
              <span>
                {[result.author_name, result.work_name].filter(Boolean).join(' - ') || 'Unknown source'}
              </span>
              {(result.volume || result.chapter || result.section) && (
                <span className="ml-2 text-base-content/70">
                  ({[
                    result.volume && `Vol. ${result.volume}`,
                    result.chapter && `Ch. ${result.chapter}`,
                    result.section && `Sec. ${result.section}`
                  ].filter(Boolean).join(', ')})
                </span>
              )}
            </div>
            
            {result.prev_sentence && (
              <div className="text-base-content/70 mb-2">{result.prev_sentence}</div>
            )}
            
            <div className="font-medium">{result.sentence_text || 'No text available'}</div>
            
            {result.next_sentence && (
              <div className="text-base-content/70 mt-2">{result.next_sentence}</div>
            )}
            
            {result.line_numbers && result.line_numbers.length > 0 && (
              <div className="mt-2 text-sm text-base-content/70">
                Line numbers: {result.line_numbers.join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button
            className="btn btn-sm"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          
          <span className="flex items-center px-4">
            Page {currentPage} of {totalPages}
          </span>
          
          <button
            className="btn btn-sm"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
