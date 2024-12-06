import { LexicalValue, Citation, CitationObject } from '../../utils/api'
import { NoResultsMetadata } from '../../utils/api/types/types'

interface ResultsDisplayProps {
  title?: string
  content: string | null | LexicalValue
  error?: string | null
  className?: string
  isHtml?: boolean
  onShowCitation?: (citation: Citation) => void
  noResultsMetadata?: NoResultsMetadata
}

function sanitizeHtml(html: string): string {
  // This is a very basic sanitization. For production, use a proper sanitization library.
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
}

function isCitationObject(citation: Citation): citation is CitationObject {
  return typeof citation !== 'string' && 'sentence' in citation;
}

function formatCitation(citation: Citation): string {
  if (!isCitationObject(citation)) {
    return citation;
  }

  const authorWork = citation.source.author && citation.source.work ? 
    `${citation.source.author}, ${citation.source.work}` :
    'Unknown Source'

  const locationParts = [
    citation.location.epistle && `Epistle ${citation.location.epistle}`,
    citation.location.fragment && `Fragment ${citation.location.fragment}`,
    citation.location.volume && `Volume ${citation.location.volume}`,
    citation.location.book && `book ${citation.location.book}`,
    citation.location.chapter && `Chapter ${citation.location.chapter}`,
    citation.location.section && `Section ${citation.location.section}`,
    citation.location.page && `Page ${citation.location.page}`,
    // Add "Line" prefix to location.line if it doesn't have it
    citation.location.line && (
      citation.location.line.includes('-')
        ? `Lines ${citation.location.line}`
        : `Line ${citation.location.line}`
    ) || (
      // Fallback to context.line_numbers if location.line is not available
      citation.context?.line_numbers?.length > 0 && (
        citation.context.line_numbers.length === 1
          ? `Line ${citation.context.line_numbers[0]}`
          : `Lines ${citation.context.line_numbers[0]}-${citation.context.line_numbers[citation.context.line_numbers.length - 1]}`
      )
    )
  ].filter(Boolean)
  
  const location = locationParts.length > 0 ? `(${locationParts.join(', ')})` : ''
  
  return location ? `${authorWork} ${location}` : authorWork
}

function isLexicalValue(content: any): content is LexicalValue {
  return content && typeof content === 'object' && 'lemma' in content
}

function CitationDisplay({ citation }: { citation: Citation }) {
  // If this is a string citation from LLM, display it simply
  if (!isCitationObject(citation)) {
    return (
      <div className="card bg-base-200 p-4">
        <div className="mt-2 text-base font-medium border-l-4 border-primary pl-4 py-2">
          {citation}
        </div>
      </div>
    )
  }

  return (
    <div className="card bg-base-200 p-4">
      {/* Citation Header */}
      <div className="flex justify-between items-start">
        <div className="font-medium">{formatCitation(citation)}</div>
      </div>
      
      {/* Previous Sentence Context */}
      {citation.sentence.prev_sentence && (
        <div className="mt-2 text-sm text-base-content/70">
          {citation.sentence.prev_sentence}
        </div>
      )}
      
      {/* Main Sentence */}
      <div className="mt-2 text-base font-medium border-l-4 border-primary pl-4 py-2">
        {citation.sentence.text}
      </div>
      
      {/* Next Sentence Context */}
      {citation.sentence.next_sentence && (
        <div className="mt-2 text-sm text-base-content/70">
          {citation.sentence.next_sentence}
        </div>
      )}
      
      {/* Additional Context - Only show if different from sentence text */}
      {citation.context.line_text && citation.context.line_text !== citation.sentence.text && (
        <div className="mt-4 text-sm">
          <span className="font-medium">Line Context: </span>
          <span className="text-base-content/70">{citation.context.line_text}</span>
        </div>
      )}
      
      {/* Reference - Only show if different from formatted citation */}
      {citation.citation && citation.citation !== formatCitation(citation) && (
        <div className="mt-2 text-sm">
          <span className="font-medium">Reference: </span>
          <span className="text-base-content/70">{citation.citation}</span>
        </div>
      )}
    </div>
  )
}

export function ResultsDisplay({
  title = 'Results',
  content,
  error,
  className = '',
  isHtml = false,
  onShowCitation,
  noResultsMetadata,
}: ResultsDisplayProps) {
  // Debug logging
  console.log('ResultsDisplay Props:', {
    title,
    content,
    error,
    noResultsMetadata
  });

  // If no results metadata is provided, show the no results display
  if (noResultsMetadata) {
    console.log('Rendering No Results Metadata:', noResultsMetadata);
    return (
      <div className={`mt-6 ${className}`}>
        <h3 className="font-bold mb-2">{title}</h3>
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
            
            {noResultsMetadata.generated_query && (
              <details className="text-yellow-700 mt-2">
                <summary>Original Query Details</summary>
                <pre className="bg-yellow-100 p-2 rounded text-xs overflow-x-auto">
                  {noResultsMetadata.generated_query}
                </pre>
              </details>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!content && !error) return null

  return (
    <div className={`mt-6 ${className}`}>
      <h3 className="font-bold mb-2">{title}</h3>
      <div className={`results-content ${error ? 'text-error' : ''}`}>
        {error ? (
          <div className="alert alert-error">{error}</div>
        ) : isLexicalValue(content) ? (
          <div className="card bg-base-100 shadow-lg">
            <div className="card-body">
              <h2 className="card-title">{content.lemma}</h2>
              {content.translation && (
                <p className="text-lg">{content.translation}</p>
              )}
              
              {(content.short_description || content.short_description) && (
                <>
                  <div className="divider">Short Description</div>
                  {content.short_description && (
                    <p className="mt-2">{content.short_description}</p>
                  )}
                </>
              )}
              
              {(content.long_description || content.long_description) && (
                <>
                  <div className="divider">Long Description</div>
                  {content.long_description && (
                    <p className="mt-2">{content.long_description}</p>
                  )}
                </>
              )}

              {content.related_terms && content.related_terms.length > 0 && (
                <>
                  <div className="divider">Related Terms</div>
                  <div className="flex flex-wrap gap-2">
                    {content.related_terms.map((term: string, index: number) => (
                      <div key={index} className="badge badge-primary">{term}</div>
                    ))}
                  </div>
                </>
              )}
              
              {content.citations_used && content.citations_used.length > 0 && (
                <>
                  <div className="divider">Citations Used</div>
                  <div className="text-sm text-base-content/80">
                    {content.citations_used.map((citation: Citation, index: number) => (
                      <p key={index} className="mb-1">{formatCitation(citation)}</p>
                    ))}
                  </div>
                </>
              )}
              
              {content.references && content.references.citations.length > 0 && (
                <>
                  <div className="divider">References</div>
                  <div className="space-y-4">                
                    {content.references.citations.map((citation: Citation, index: number) => (
                      <CitationDisplay 
                        key={index} 
                        citation={citation}
                      />
                    ))}
                  </div>
                </>
              )}

              {/* Metadata and Version Info */}
              {(content.created_at || content.updated_at || content.version || content.metadata) && (
                <>
                  <div className="divider">Version and Metadata</div>
                  <div className="text-sm">
                    {content.created_at && (
                      <p>Created: {new Date(content.created_at).toLocaleString()}</p>
                    )}
                    {content.updated_at && (
                      <p>Updated: {new Date(content.updated_at).toLocaleString()}</p>
                    )}
                    {content.version && (
                      <p>Version: {content.version}</p>
                    )}

                    {/* Enhanced Metadata Rendering */}
                    {content.metadata && (
                      <div className="mt-2">
                        <h4 className="font-semibold">Metadata Details</h4>
                        
                        {/* Render LLM Configuration if available */}
                        {content.metadata.llm_config && Object.keys(content.metadata.llm_config).length > 0 && (
                          <div className="mt-2">
                            <h5 className="font-medium">LLM Configuration</h5>
                            <div className="grid grid-cols-2 gap-1">
                              {Object.entries(content.metadata.llm_config).map(([key, value]) => (
                                <div key={key}>
                                  {key}: {typeof value === 'object' ? JSON.stringify(value) : value}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Render other metadata fields */}
                        {Object.entries(content.metadata)
                          .filter(([key]) => key !== 'llm_config')
                          .map(([key, value]) => (
                            <div key={key} className="mt-1">
                              <span className="font-medium">{key}:</span>{' '}
                              {typeof value === 'object' 
                                ? JSON.stringify(value, null, 2) 
                                : String(value)}
                            </div>
                          ))}

                        {/* Full Metadata Details */}
                        <details className="mt-2">
                          <summary className="font-semibold cursor-pointer">Full Metadata</summary>
                          <pre className="bg-base-200 p-2 rounded text-xs overflow-x-auto">
                            {JSON.stringify(content.metadata, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        ) : isHtml ? (
          <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(content as string || '') }} />
        ) : (
          content
        )}
      </div>
    </div>
  )
}

interface ProgressDisplayProps {
  current: number
  total: number
  className?: string
}

export function ProgressDisplay({
  current,
  total,
  className = '',
}: ProgressDisplayProps) {
  if (total === 0) return null

  return (
    <div className={`progress-container ${className}`}>
      <div className="flex justify-between mb-1">
        <span className="text-sm">Progress:</span>
        <span className="text-sm progress-text">{current}/{total}</span>
      </div>
      <progress
        className="progress progress-primary w-full"
        value={(current / total) * 100}
        max="100"
      />
    </div>
  )
}
