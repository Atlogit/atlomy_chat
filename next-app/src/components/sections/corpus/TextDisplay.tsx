'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { ResultsDisplay } from '@/components/ui/ResultsDisplay'
import { useLoading } from '@/hooks/useLoading'
import { fetchApi, API } from '@/utils/api'

interface TextContent {
  id: string
  title: string
  author?: string
  language?: string
  content: string
  metadata?: {
    [key: string]: string
  }
}

interface TextDisplayProps {
  textId: string
}

export function TextDisplay({ textId }: TextDisplayProps) {
  const [text, setText] = useState<TextContent | null>(null)
  const { isLoading, error, execute } = useLoading<TextContent>()

  useEffect(() => {
    loadText()
  }, [textId])

  const loadText = async () => {
    const result = await execute(
      fetchApi<TextContent>(`${API.corpus.all}/${encodeURIComponent(textId)}`)
    )

    if (result) {
      setText(result)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center p-4">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    )
  }

  if (error) {
    return <ResultsDisplay error={error} content={null} />
  }

  if (!text) {
    return (
      <div className="text-center py-8">
        <p className="text-base-content/70">Text not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-header space-y-2">
        <h3 className="text-2xl font-bold">{text.title}</h3>
        {text.author && (
          <p className="text-base-content/70">by {text.author}</p>
        )}
        {text.language && (
          <div className="badge badge-outline">{text.language}</div>
        )}
      </div>

      {text.metadata && Object.keys(text.metadata).length > 0 && (
        <div className="metadata-section card bg-base-200">
          <div className="card-body">
            <h4 className="card-title text-lg">Metadata</h4>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(text.metadata).map(([key, value]) => (
                <div key={key} className="metadata-item">
                  <span className="font-medium">{key}:</span>{' '}
                  <span className="text-base-content/70">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="text-content card bg-base-200">
        <div className="card-body">
          <div className="prose max-w-none">
            {text.content.split('\n').map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
