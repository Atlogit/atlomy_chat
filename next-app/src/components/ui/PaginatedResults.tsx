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

type LocationField = 'book' | 'fragment' | 'volume' | 'page' | 'chapter' | 'section' | 'line'
type AvailableFields = Record<LocationField, string | null>

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
    // More strict checking for source properties
    if (!result.source || typeof result.source !== 'object') {
      return 'Unknown Source'
    }

    const { author, work } = result.source
    if (!author || !work || author === 'Unknown' || work === 'Unknown') {
      return 'Unknown Source'
    }

    const authorWork = `${author}, ${work}`
    const locationParts: string[] = []

    // Get all available location fields
    const location = result.location || {}
    const availableFields: AvailableFields = {
      book: location.book ? `book ${location.book}` : null,
      fragment: location.fragment ? `Fragment ${location.fragment}` : null,
      volume: location.volume ? `Volume ${location.volume}` : null,
      page: location.page ? `Page ${location.page}` : null,
      chapter: location.chapter ? `Chapter ${location.chapter}` : null,
      section: location.section ? `Section ${location.section}` : null,
      line: result.context?.line_numbers?.length ? (
        result.context.line_numbers.length === 1 
          ? `Line ${result.context.line_numbers[0]}`
          : `Lines ${result.context.line_numbers[0]}-${result.context.line_numbers[result.context.line_numbers.length - 1]}`
      ) : null
    }

    // Add fields in the order they appear in the work structure
    // This ensures we respect the citation format for each work
    const fieldOrder: LocationField[] = ['book', 'fragment', 'volume', 'page', 'chapter', 'section', 'line']
    fieldOrder.forEach(field => {
      const value = availableFields[field]
      if (value) {
        locationParts.push(value)
      }
    })
    
    const locationStr = locationParts.length > 0 ? ` (${locationParts.join(', ')})` : ''
    
    return `${authorWork}${locationStr}`
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
          <div key={`${result.sentence?.id || index}-${index}`} className="card bg-base-200 p-4">
            {/* Citation Header */}
            <div className="flex justify-between items-start">
              <div className="font-medium">{formatCitation(result)}</div>
            </div>
            
            {/* Previous Sentence Context */}
            {result.sentence?.prev_sentence && (
              <div className="mt-2 text-sm text-base-content/70">
                {result.sentence.prev_sentence}
              </div>
            )}
            
            {/* Main Sentence */}
            <div className="mt-2 text-base font-medium border-l-4 border-primary pl-4 py-2">
              {result.sentence?.text || 'No text available'}
            </div>
            
            {/* Next Sentence Context */}
            {result.sentence?.next_sentence && (
              <div className="mt-2 text-sm text-base-content/70">
                {result.sentence.next_sentence}
              </div>
            )}
            
            {/* Line Context - Only show if different from sentence text */}
            {result.context?.line_text && result.sentence?.text && 
             result.context.line_text !== result.sentence.text && (
              <div className="mt-4 text-sm">
                <span className="font-medium">Line Context: </span>
                <span className="text-base-content/70">{result.context.line_text}</span>
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
