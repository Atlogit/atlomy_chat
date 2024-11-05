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

  const formatCitation = (result: SearchResult): string => {
    const authorWork = result.author_name && result.work_name ? 
      `${result.author_name}, ${result.work_name}` :
      'Unknown Source'

    const locationParts = [
      result.volume && `Volume ${result.volume}`,
      result.chapter && `Chapter ${result.chapter}`,
      result.section && `Section ${result.section}`,
      result.line_numbers?.length > 0 && (
        result.line_numbers.length === 1 
          ? `Line ${result.line_numbers[0]}`
          : `Lines ${result.line_numbers[0]}-${result.line_numbers[result.line_numbers.length - 1]}`
      )
    ].filter(Boolean)
    
    const location = locationParts.length > 0 ? `(${locationParts.join(', ')})` : ''
    
    return location ? `${authorWork} ${location}` : authorWork
  }

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
          <div key={`${result.sentence_id || index}-${index}`} className="card bg-base-200 p-4">
            {/* Citation Header */}
            <div className="flex justify-between items-start">
              <div className="font-medium">{formatCitation(result)}</div>
            </div>
            
            {/* Previous Sentence Context */}
            {result.prev_sentence && (
              <div className="mt-2 text-sm text-base-content/70">
                {result.prev_sentence}
              </div>
            )}
            
            {/* Main Sentence */}
            <div className="mt-2 text-base font-medium border-l-4 border-primary pl-4 py-2">
              {result.sentence_text || 'No text available'}
            </div>
            
            {/* Next Sentence Context */}
            {result.next_sentence && (
              <div className="mt-2 text-sm text-base-content/70">
                {result.next_sentence}
              </div>
            )}
            
            {/* Line Context - Only show if different from sentence text */}
            {result.line_text && result.line_text !== result.sentence_text && (
              <div className="mt-4 text-sm">
                <span className="font-medium">Line Context: </span>
                <span className="text-base-content/70">{result.line_text}</span>
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
