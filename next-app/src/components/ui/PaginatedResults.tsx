import { useState, useEffect } from 'react'
import { LexicalValue } from '../../utils/api'
import { ResultsDisplay } from './ResultsDisplay'

interface PaginatedResultsProps {
  title?: string
  results: any[]
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
  const [paginatedResults, setPaginatedResults] = useState<LexicalValue | null>(null)
  const totalPages = Math.ceil(results.length / pageSize)

  useEffect(() => {
    if (!results.length) {
      setPaginatedResults(null)
      return
    }

    const start = (currentPage - 1) * pageSize
    const end = start + pageSize
    const pageResults = results.slice(start, end)

    // Create a LexicalValue structure for the paginated results
    const lexicalValue: LexicalValue = {
      id: `query-results-page-${currentPage}`,
      lemma: `Results (Page ${currentPage} of ${totalPages})`,
      categories: [],
      analyses: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      version: '1.0',
      citations_used: pageResults.map(result => ({
        sentence: {
          id: result.sentence_id || '',
          text: result.sentence_text || result.text || '',
          prev_sentence: result.prev_sentence || '',
          next_sentence: result.next_sentence || '',
          tokens: result.tokens || {}
        },
        citation: result.citation || '',
        context: {
          line_id: result.line_id || '',
          line_text: result.line_text || '',
          line_numbers: result.line_numbers || []
        },
        location: {
          volume: result.volume || '',
          chapter: result.chapter || '',
          section: result.section || ''
        },
        source: {
          author: result.author || '',
          work: result.work || ''
        }
      }))
    }

    setPaginatedResults(lexicalValue)
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
    return null
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between items-center">
        <h3 className="font-bold">{title}</h3>
        <div className="text-sm text-base-content/70">
          Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, results.length)} of {results.length} results
        </div>
      </div>

      <ResultsDisplay
        content={paginatedResults}
        className="p-4 bg-base-200 rounded-lg"
      />

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
