import React, { useState, useEffect, useCallback } from 'react'
import { SearchResult, ProcessingStatus, NoResultsMetadata } from '../../utils/api/types/types'
import { ProgressIndicator, LoadingSpinner, ErrorDisplay } from './ProgressIndicator'
import { API } from '../../utils/api/endpoints'
import { fetchApi } from '../../utils/api/fetch'

interface PaginatedResultsProps {
  title?: string
  results: SearchResult[]
  pageSize?: number
  className?: string
  isLoading?: boolean
  processingStatus?: ProcessingStatus
  onPageChange?: (page: number, pageSize: number) => Promise<SearchResult[]>
  totalResults?: number
  noResultsMetadata?: NoResultsMetadata  // New optional prop
}

type LocationField = 'epistle' | 'fragment' | 'volume' | 'book' | 'chapter' | 'section' | 'page' | 'line'
type AvailableFields = Record<LocationField, string | null>

export function PaginatedResults({
  title = 'Results',
  results,
  pageSize = 10,
  className = '',
  isLoading = false,
  processingStatus,
  onPageChange,
  totalResults,
  noResultsMetadata,  // Add to destructured props
}: PaginatedResultsProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [paginatedResults, setPaginatedResults] = useState<SearchResult[]>([])
  const [isChangingPage, setIsChangingPage] = useState(false)
  const [pollingStatus, setPollingStatus] = useState<ProcessingStatus | null>(processingStatus || null)
  const [isPolling, setIsPolling] = useState(!!processingStatus)
  
  // Debugging logging
  useEffect(() => {
    console.group('PaginatedResults Debug')
    console.log('Results:', results)
    console.log('Processing Status:', processingStatus)
    console.log('Total Results:', totalResults)
    console.log('Is Loading:', isLoading)
    console.log('Current Page:', currentPage)
    console.log('Paginated Results:', paginatedResults)
    console.log('Is Polling:', isPolling)
    console.groupEnd()
  }, [results, processingStatus, totalResults, isLoading, currentPage, paginatedResults, isPolling])
  
  // Calculate total pages based on totalResults if provided, otherwise use results.length
  const totalPages = totalResults 
    ? Math.ceil(totalResults / pageSize)
    : Math.ceil(results.length / pageSize)

  // Polling mechanism for processing status
  const pollQueryStatus = useCallback(async () => {
    if (!pollingStatus?.results_id) {
      console.warn('No results_id found for polling');
      return;
    }

    try {
      console.log('Polling query status for ID:', pollingStatus.results_id);
      const status = await fetchApi<ProcessingStatus>(API.llm.checkQueryStatus, {
        method: 'POST',
        body: JSON.stringify({ results_id: pollingStatus.results_id })
      });

      console.log('Polling status result:', status);
      setPollingStatus(status);

      if (status.status === 'completed') {
        setIsPolling(false);
        // Trigger initial page load
        if (onPageChange) {
          try {
            const initialResults = await onPageChange(1, pageSize);
            console.log('Initial results from page change:', initialResults);
            setPaginatedResults(initialResults);
          } catch (pageChangeError) {
            console.error('Error in page change during polling:', pageChangeError);
          }
        }
      } else if (status.status === 'failed') {
        setIsPolling(false);
        // Handle error state
        console.error('Query processing failed', status);
      }
    } catch (error) {
      console.error('Error polling query status', error);
      setIsPolling(false);
    }
  }, [pollingStatus?.results_id, onPageChange, pageSize]);

  // Start polling when processing status is received
  useEffect(() => {
    if (processingStatus) {
      console.log('Starting polling with status:', processingStatus);
      setPollingStatus(processingStatus);
      setIsPolling(true);
    }
  }, [processingStatus]);

  // Polling interval effect
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    if (isPolling) {
      intervalId = setInterval(pollQueryStatus, 5000); // Poll every 5 seconds
      console.log('Polling interval started');
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
        console.log('Polling interval cleared');
      }
    };
  }, [isPolling, pollQueryStatus]);

  // Update results when initial results change
  useEffect(() => {
    console.log('Results changed:', results);
    if (!results.length) {
      setPaginatedResults([])
      return
    }

    // Only set initial results if we're not using server pagination
    // or if we're on the first page
    if (!onPageChange || currentPage === 1) {
      setPaginatedResults(results)
    }
  }, [results, onPageChange, currentPage])

  const handlePageChange = async (newPage: number) => {
    console.log(`Changing to page ${newPage}`);
    if (onPageChange) {
      setIsChangingPage(true)
      try {
        const newResults = await onPageChange(newPage, pageSize)
        console.log(`Results for page ${newPage}:`, newResults);
        setPaginatedResults(newResults)
        setCurrentPage(newPage)
      } catch (error) {
        console.error('Error changing page:', error)
      } finally {
        setIsChangingPage(false)
      }
    } else {
      // Client-side pagination
      setCurrentPage(newPage)
      const start = (newPage - 1) * pageSize
      const end = start + pageSize
      const pageResults = results.slice(start, end)
      setPaginatedResults(pageResults)
    }
  }

  // (formatCitation method and rendering logic)

  // Processing status rendering
  if (isPolling) {
    const processedCitations = pollingStatus?.processed_citations ?? 0;
    const totalCitations = pollingStatus?.total_citations ?? 0;

    return (
      <div className={`space-y-4 ${className}`}>
        <ProgressIndicator 
          current={processedCitations}
          total={totalCitations}
          stage={pollingStatus?.status || 'Processing results'}
          className="px-4"
        />
        {pollingStatus?.status === 'failed' && (
          <ErrorDisplay 
            message="Query processing encountered an error"
            onRetry={() => {
              // Implement retry logic if needed
              setIsPolling(true);
              pollQueryStatus();
            }}
          />
        )}
      </div>
    )
  }

  // Existing loading and no results states
  if (isLoading || isChangingPage) {
    return (
      <div className={`space-y-4 ${className}`}>
        <LoadingSpinner 
          message={isChangingPage ? 'Loading more results...' : 'Loading results...'}
        />
      </div>
    )
  }

  // If no results and noResultsMetadata is provided, show detailed no-results information
  if (!results.length && noResultsMetadata) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="card bg-yellow-50 border border-yellow-200 p-4 mb-4">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">No Results Found</h3>
          
          <div className="space-y-2">
            <p className="text-yellow-700">
              <strong>Search Description:</strong> {noResultsMetadata.search_description}
            </p>
            
            <div className="bg-yellow-100 rounded p-2">
              <h4 className="font-medium text-yellow-900">Search Criteria:</h4>
              <ul className="list-disc list-inside text-yellow-800">
                {Object.entries(noResultsMetadata.search_criteria).map(([key, value]) => (
                  <li key={key}>
                    {key}: <span className="font-semibold">{value}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <details className="text-yellow-700 mt-2">
              <summary>Original Query Details</summary>
              <pre className="bg-yellow-100 p-2 rounded text-xs overflow-x-auto">
                {noResultsMetadata.generated_query}
              </pre>
            </details>
          </div>
        </div>
      </div>
    )
  }

  // Existing no results state
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
          Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalResults || results.length)} of {totalResults || results.length} results
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
            onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1 || isChangingPage}
          >
            Previous
          </button>
          
          <span className="flex items-center px-4">
            Page {currentPage} of {totalPages}
          </span>
          
          <button
            className="btn btn-sm"
            onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages || isChangingPage}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

function formatCitation(result: SearchResult): string {
  // First, check for a pre-existing full citation
  if (result.citation) {
    return result.citation
  }

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
    epistle: location.epistle ? `Epistle ${location.epistle}` : null,
    fragment: location.fragment ? `Fragment ${location.fragment}` : null,
    volume: location.volume ? `Volume ${location.volume}` : null,
    book: location.book ? `book ${location.book}` : null,
    chapter: location.chapter ? `Chapter ${location.chapter}` : null,
    section: location.section ? `Section ${location.section}` : null,
    page: location.page ? `Page ${location.page}` : null,
    line: result.context?.line_numbers?.length ? (
      result.context.line_numbers.length === 1 
        ? `Line ${result.context.line_numbers[0]}`
        : `Lines ${result.context.line_numbers[0]}-${result.context.line_numbers[result.context.line_numbers.length - 1]}`
    ) : null
  }

  // Add fields in the order they appear in the work structure
  // This ensures we respect the citation format for each work
  const fieldOrder: LocationField[] = ['epistle', 'fragment', 'book', 'volume', 'page', 'chapter', 'section', 'line']
  fieldOrder.forEach(field => {
    const value = availableFields[field]
    if (value) {
      locationParts.push(value)
    }
  })
  
  const locationStr = locationParts.length > 0 ? ` (${locationParts.join(', ')})` : ''
  
  return `${authorWork}${locationStr}`
}
