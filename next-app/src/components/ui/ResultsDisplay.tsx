interface ResultsDisplayProps {
  title?: string
  content: string | null
  error?: string | null
  className?: string
  isHtml?: boolean
}

function sanitizeHtml(html: string): string {
  // This is a very basic sanitization. For production, use a proper sanitization library.
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
}

export function ResultsDisplay({
  title = 'Results',
  content,
  error,
  className = '',
  isHtml = false,
}: ResultsDisplayProps) {
  if (!content && !error) return null

  return (
    <div className={`mt-6 ${className}`}>
      <h3 className="font-bold mb-2">{title}</h3>
      <div className={`results-content ${error ? 'text-error' : ''}`}>
        {error || (
          isHtml ? (
            <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(content || '') }} />
          ) : (
            content
          )
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
