'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API } from '../../../utils/api'

interface CorpusText {
  id?: string
  title: string
  author?: string
  language?: string
  description?: string
}

type ApiResponse = CorpusText[] | { texts: CorpusText[] } | Record<string, never>

interface ListTextsProps {
  onTextSelect: (textId: string) => void
}

export function ListTexts({ onTextSelect }: ListTextsProps) {
  const [texts, setTexts] = useState<CorpusText[]>([])
  const { data, error, isLoading, execute } = useApi<ApiResponse>()

  useEffect(() => {
    console.log('ListTexts component mounted')
    loadTexts()
  }, [])

  useEffect(() => {
    console.log('Data received from API:', data)
    if (data) {
      if (Array.isArray(data)) {
        console.log('Setting texts from array:', data)
        setTexts(data)
      } else if (typeof data === 'object' && 'texts' in data && Array.isArray(data.texts)) {
        console.log('Setting texts from object:', data.texts)
        setTexts(data.texts)
      } else if (typeof data === 'object' && Object.keys(data).length === 0) {
        console.warn('API returned an empty object')
        setTexts([])
      } else {
        console.error('Unexpected API response format:', data)
        setTexts([])
      }
    }
  }, [data])

  const loadTexts = async () => {
    console.log('Executing API call')
    await execute(API.corpus.list)
  }

  console.log('Current texts state:', texts)

  if (isLoading) {
    return (
      <div className="flex justify-center p-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    console.error('Error loading texts:', error)
    return <ResultsDisplay error={`Error loading texts: ${error.message}`} content={null} />
  }

  const getUniqueKey = (text: CorpusText, index: number) => {
    if (text.id) return `text-${text.id}`
    if (text.title) return `text-${text.title.slice(0, 20)}-${index}`
    return `text-${index}`
  }

  return (
    <div className="space-y-4">
      {texts.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-base-content/70">No texts available. The corpus may be empty.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {texts.map((text, index) => (
            <div key={getUniqueKey(text, index)} className="card bg-base-200">
              <div className="card-body">
                <h3 className="card-title text-lg">
                  {text.title}
                  {text.author && (
                    <span className="text-base-content/70 text-sm">
                      by {text.author}
                    </span>
                  )}
                </h3>
                <React.Fragment key={`details-${getUniqueKey(text, index)}`}>
                  {text.description && (
                    <p className="text-base-content/70">{text.description}</p>
                  )}
                  {text.language && (
                    <div className="badge badge-outline">{text.language}</div>
                  )}
                </React.Fragment>
                <div className="card-actions justify-end mt-2">
                  <Button
                    onClick={() => onTextSelect(text.id || `fallback-${index}`)}
                    variant="outline"
                  >
                    View Text
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
