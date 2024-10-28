'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, Text, TextDivision } from '../../../utils/api'

interface ListTextsProps {
  onTextSelect: (textId: string) => void
}

export function ListTexts({ onTextSelect }: ListTextsProps) {
  const [texts, setTexts] = useState<Text[]>([])
  const { data, error, isLoading, execute } = useApi<Text[]>()

  useEffect(() => {
    loadTexts()
  }, [])

  useEffect(() => {
    if (data) {
      setTexts(data)
    }
  }, [data])

  const loadTexts = async () => {
    await execute(API.corpus.list)
  }

  if (isLoading) {
    return (
      <div className="flex justify-center p-4">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    )
  }

  if (error) {
    return <ResultsDisplay error={`Error loading texts: ${error.message}`} content={null} />
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
    
    if (division.author_id_field) {
      parts.push(`[${division.author_id_field}]`)
    }
    if (division.work_number_field) {
      parts.push(`[${division.work_number_field}]`)
    }
    if (division.epithet_field) {
      parts.push(`[${division.epithet_field}]`)
    }
    if (division.fragment_field) {
      parts.push(`(fr. ${division.fragment_field})`)
    }

    return parts.join(' ')
  }

  const renderStructureInfo = (divisions: TextDivision[]) => {
    const structure = new Set<string>()
    
    divisions.forEach(div => {
      if (div.volume) structure.add('Volumes')
      if (div.chapter) structure.add('Chapters')
      if (div.section) structure.add('Sections')
      if (div.line) structure.add('Lines')
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

  return (
    <div className="space-y-4">
      {texts.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-base-content/70">No texts available. The corpus may be empty.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {texts.map((text) => (
            <div key={getUniqueKey(text)} className="card bg-base-200">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="card-title text-lg">
                      {text.title}
                      {text.author && (
                        <span className="text-base-content/70 text-sm ml-2">
                          by {text.author}
                        </span>
                      )}
                    </h3>
                    <div className="text-sm font-mono text-base-content/70 mt-1">
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
      )}
    </div>
  )
}
