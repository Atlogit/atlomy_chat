import { LexicalValue, Citation, CitationObject } from '../../utils/api'

interface ResultsDisplayProps {
  title?: string
  content: string | null | LexicalValue
  error?: string | null
  className?: string
  isHtml?: boolean
  onShowCitation?: (citation: Citation) => void
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
    citation.location.volume && `Volume ${citation.location.volume}`,
    citation.location.chapter && `Chapter ${citation.location.chapter}`,
    citation.location.section && `Section ${citation.location.section}`,
    citation.context.line_numbers?.length > 0 && `Line${citation.context.line_numbers.length > 1 ? 's' : ''} ${citation.context.line_numbers.join(', ')}`
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
}: ResultsDisplayProps) {
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
              
              {(content.created_at || content.updated_at || content.version) && (
                <>
                  <div className="divider">Version Info</div>
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
