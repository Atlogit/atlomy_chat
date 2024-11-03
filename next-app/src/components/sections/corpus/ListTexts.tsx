'use client'

import React, { useEffect, useRef } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, Text, TextDivision } from '../../../utils/api'

interface ListTextsProps {
  onTextSelect: (textId: string) => void
  texts: Text[]
  setTexts: React.Dispatch<React.SetStateAction<Text[]>>
}

export function ListTexts({ onTextSelect, texts, setTexts }: ListTextsProps) {
  const [loadingProgress, setLoadingProgress] = React.useState<number>(0)
  const { data, error, isLoading, execute } = useApi<Text[]>()
  const abortControllerRef = useRef<AbortController | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  useEffect(() => {
    if (data) {
      setTexts(data)
      setLoadingProgress(100) // Complete the loading animation
    }
  }, [data, setTexts])

  // Simulate loading progress
  useEffect(() => {
    if (isLoading && loadingProgress < 90) {
      const interval = setInterval(() => {
        setLoadingProgress(prev => Math.min(prev + 10, 90))
      }, 500)
      return () => clearInterval(interval)
    }
  }, [isLoading, loadingProgress])

  const loadTexts = async () => {
    setLoadingProgress(0)
    abortControllerRef.current = new AbortController()
    await execute(API.corpus.list, {
      signal: abortControllerRef.current.signal
    })
  }

  const getUniqueKey = (text: Text) => {
    return `text-${text.id}`
  }

  const renderMetadata = (text: Text) => {
    if (!text.metadata) return null

    const importantFields = ['language', 'period', 'genre', 'source']
    const displayFields = Object.entries(text.metadata)
      .filter(([key]) => importantFields.includes(key))

    if (displayFields.length === 0) return null

    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {displayFields.map(([key, value]) => (
          <div key={key} className="badge badge-outline badge-sm">
            {key}: {String(value)}
          </div>
        ))}
      </div>
    )
  }

  const renderCitationInfo = (division: TextDivision) => {
    const parts = []
    
    if (division.author_name) {
      parts.push(division.author_name)
    }
    if (division.work_name) {
      parts.push(division.work_name)
    }

    // Add structural information if available
    const structural = []
    if (division.volume) structural.push(`Vol. ${division.volume}`)
    if (division.chapter) structural.push(`Ch. ${division.chapter}`)
    if (division.section) structural.push(`§${division.section}`)
    
    if (structural.length > 0) {
      parts.push(structural.join(', '))
    }

    return parts.join(' ')
  }

  const renderStructureInfo = (divisions: TextDivision[]) => {
    const structure = new Set<string>()
    
    divisions.forEach(div => {
      if (div.volume) structure.add('Volumes')
      if (div.chapter) structure.add('Chapters')
      if (div.section) structure.add('Sections')
      if (div.lines?.length) structure.add('Lines')
      if (div.is_title) structure.add('Titles')
    })

    return Array.from(structure).join(' • ')
  }

  const getDivisionCount = (divisions: TextDivision[]) => {
    const counts = {
      total: divisions.length,
      titles: divisions.filter(d => d.is_title).length
    }
    return `${counts.total} divisions${counts.titles > 0 ? ` (${counts.titles} titles)` : ''}`
  }

  const renderTextPreview = (text: Text) => {
    if (!text.text_content) return null
    
    // Show first 200 characters of text content with ellipsis
    const preview = text.text_content.slice(0, 200)
    return preview.length < text.text_content.length 
      ? `${preview}...` 
      : preview
  }

  const renderLoadingState = () => (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <div className="w-64 h-4 bg-base-200 rounded-full overflow-hidden">
        <div 
          className="h-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${loadingProgress}%` }}
        />
      </div>
      <div className="text-base-content/70">
        Loading corpus... {loadingProgress}%
      </div>
      {texts.length > 0 && (
        <div className="text-base-content/70">
          {texts.length} texts loaded
        </div>
      )}
    </div>
  )

  if (error) {
    return <ResultsDisplay error={`Error loading texts: ${error.message}`} content={null} />
  }

  return (
    <div className="space-y-4">
      {texts.length === 0 ? (
        <div className="text-center py-8">
          {isLoading ? (
            renderLoadingState()
          ) : (
            <>
              <p className="text-base-content/70 mb-4">No texts available. Click the button below to load the corpus.</p>
              <Button onClick={loadTexts} variant="primary">
                Load Corpus
              </Button>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Text count header */}
          <div className="flex justify-between items-center">
            <div className="text-base-content/70">
              {texts.length} texts loaded
            </div>
            {isLoading && (
              <div className="flex items-center gap-2">
                <span className="loading loading-spinner loading-sm"></span>
                <span className="text-sm">Loading more...</span>
              </div>
            )}
          </div>

          {/* Text cards */}
          <div className="grid gap-4">
            {texts.map((text) => (
              <div key={getUniqueKey(text)} className="card bg-base-200">
                <div className="card-body">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="card-title text-lg">
                        {text.work_name}
                      </h3>
                      {text.author && (
                        <div className="text-lg mt-1">
                          Author: {text.author}
                        </div>
                      )}
                      <div className="text-sm font-mono text-base-content/70 mt-2">
                        {text.reference_code && (
                          <div>Reference: {text.reference_code}</div>
                        )}
                        {text.divisions && text.divisions[0] && (
                          <div>Citation: {renderCitationInfo(text.divisions[0])}</div>
                        )}
                      </div>
                    </div>
                    <Button
                      onClick={() => onTextSelect(text.id)}
                      variant="outline"
                      className="btn-sm"
                    >
                      View Text
                    </Button>
                  </div>

                  {/* Text Preview */}
                  {text.text_content && (
                    <div className="mt-2 text-sm text-base-content/70">
                      <p className="line-clamp-2">{renderTextPreview(text)}</p>
                    </div>
                  )}

                  {/* Metadata Display */}
                  {renderMetadata(text)}

                  {/* Division Summary */}
                  {text.divisions && text.divisions.length > 0 && (
                    <div className="mt-4 text-sm text-base-content/70">
                      <div className="font-medium">Structure: {renderStructureInfo(text.divisions)}</div>
                      <div className="mt-1 text-xs">
                        {getDivisionCount(text.divisions)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
