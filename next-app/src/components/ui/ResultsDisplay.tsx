import { LexicalValue, Citation } from '../../utils/api'

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

function formatCitation(citation: Citation): string {
  const authorWork = `${citation.source.author}, ${citation.source.work}`
  const location = [
    citation.location.volume && `Volume ${citation.location.volume}`,
    citation.location.chapter && `Chapter ${citation.location.chapter}`,
    citation.location.section && `Section ${citation.location.section}`,
    citation.context.line_numbers && `Lines ${citation.context.line_numbers.join(', ')}`
  ].filter(Boolean).join(', ')
  
  return `${authorWork} (${location})`
}

function isLexicalValue(content: any): content is LexicalValue {
  return content && typeof content === 'object' && 'lemma' in content
}

function CitationDisplay({ citation }: { citation: Citation }) {
  return (
    <div className="card bg-base-200 p-4">
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
      
      {/* Additional Context */}
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-medium">Line Context:</span>
          <div className="text-base-content/70">{citation.context.line_text}</div>
        </div>
        <div>
          <span className="font-medium">Reference:</span>
          <div className="text-base-content/70">{citation.citation}</div>
        </div>
      </div>
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
              
              {(content.short_description || content.long_description) && (
                <>
                  <div className="divider">Description</div>
                  {content.short_description && (
                    <p>{content.short_description}</p>
                  )}
                  {content.long_description && (
                    <p className="mt-2">{content.long_description}</p>
                  )}
                </>
              )}
              
              {content.citations_used && content.citations_used.length > 0 && (
                <>
                  <div className="divider">Citations</div>
                  <div className="space-y-4">
                    {content.citations_used.map((citation: Citation, index: number) => (
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
