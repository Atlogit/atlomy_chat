'use client'

import { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useLoading } from '../../../hooks/useLoading'
import { fetchApi, API, Text, TextDivision, TextLine, TokenInfo, SpacyTokens } from '../../../utils/api'

interface TextDisplayProps {
  textId: string
}

export function TextDisplay({ textId }: TextDisplayProps) {
  const [text, setText] = useState<Text | null>(null)
  const { isLoading, error, execute } = useLoading<Text>()

  useEffect(() => {
    loadText()
  }, [textId])

  const loadText = async () => {
    const result = await execute(
      fetchApi<Text>(API.corpus.text(textId))
    )

    if (result) {
      setText(result)
    }
  }

  const renderCitation = (division: TextDivision) => {
    const parts = []
    
    // Citation components
    if (division.author_name) {
      parts.push(division.author_name)
    }
    if (division.work_name) {
      parts.push(division.work_name)
    }
    
    // Structural components
    const structural = []
    if (division.volume) structural.push(`Vol. ${division.volume}`)
    if (division.chapter) structural.push(`Ch. ${division.chapter}`)
    if (division.section) structural.push(`§${division.section}`)
    
    if (structural.length > 0) {
      parts.push(structural.join(', '))
    }
    
    return parts.join(' ')
  }

  const renderSpacyTokens = (line: TextLine) => {
    if (!line.spacy_tokens) return null

    // Handle both array and object formats
    let tokens: TokenInfo[] = []
    if (Array.isArray(line.spacy_tokens)) {
      tokens = line.spacy_tokens
    } else {
      const spacyTokens = line.spacy_tokens as SpacyTokens
      if (spacyTokens.tokens && Array.isArray(spacyTokens.tokens)) {
        tokens = spacyTokens.tokens
      }
    }

    // Filter interesting tokens
    const filteredTokens = tokens.filter(token => 
      !token.is_stop && 
      (token.pos === 'NOUN' || token.pos === 'VERB' || token.pos === 'ADJ')
    )

    if (filteredTokens.length === 0) return null

    return (
      <div className="flex flex-wrap gap-1 mt-1">
        {filteredTokens.map((token: TokenInfo, index: number) => (
          <span 
            key={`${token.text}-${index}`}
            className="text-xs px-1 py-0.5 rounded bg-base-300"
            title={`POS: ${token.pos}, Lemma: ${token.lemma}`}
          >
            {token.text}
          </span>
        ))}
      </div>
    )
  }

  const renderDivision = (division: TextDivision) => {
    return (
      <div key={division.id} className="division-content card bg-base-200 mb-4">
        <div className="card-body">
          {/* Citation and Title Section */}
          <div className="flex flex-wrap justify-between items-start gap-4 mb-4">
            <div className="citation-info">
              <span className="text-sm font-mono bg-base-300 px-2 py-1 rounded">
                {renderCitation(division)}
              </span>
            </div>
            {division.is_title && (
              <div className="title-info flex items-center gap-2">
                <span className="badge badge-primary">Title</span>
                {division.title_text && (
                  <span className="text-sm font-mono">{division.title_text}</span>
                )}
              </div>
            )}
          </div>

          {/* Title Text if present */}
          {division.title_text && (
            <h4 className="text-lg font-semibold mb-4">{division.title_text}</h4>
          )}

          {/* Text Lines */}
          <div className="prose max-w-none">
            {division.lines?.map((line: TextLine) => (
              <div key={line.line_number} className="flex gap-4 py-2 hover:bg-base-300 rounded transition-colors">
                <span className="text-sm text-base-content/50 w-12 text-right font-mono">
                  {line.line_number}
                </span>
                <div className="flex-1">
                  <p className="my-0">{line.content}</p>
                  {/* Categories */}
                  {line.categories && line.categories.length > 0 && (
                    <div className="flex gap-1 mt-1">
                      {line.categories.map((category: string) => (
                        <span key={category} className="badge badge-sm badge-ghost">
                          {category}
                        </span>
                      ))}
                    </div>
                  )}
                  {/* spaCy Token Analysis */}
                  {renderSpacyTokens(line)}
                </div>
              </div>
            ))}
          </div>

          {/* Division Metadata */}
          {division.metadata && Object.keys(division.metadata).length > 0 && (
            <div className="mt-4 pt-4 border-t border-base-300">
              <h5 className="text-sm font-semibold mb-2">Division Metadata</h5>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(division.metadata).map(([key, value]) => (
                  <div key={key}>
                    <span className="font-medium">{key}:</span>{' '}
                    <span className="text-base-content/70">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
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
      {/* Text Header */}
      <div className="text-header space-y-2">
        <h3 className="text-2xl font-bold">
          {text.work_name || text.title}
          {text.title !== text.work_name && text.title && (
            <span className="text-base-content/70 text-lg ml-2">
              ({text.title})
            </span>
          )}
        </h3>
        {text.author && (
          <p className="text-base-content/70">by {text.author}</p>
        )}
        {text.reference_code && (
          <div className="badge badge-outline">{text.reference_code}</div>
        )}
      </div>

      {/* Text Metadata */}
      {text.metadata && Object.keys(text.metadata).length > 0 && (
        <div className="metadata-section card bg-base-200">
          <div className="card-body">
            <h4 className="card-title text-lg">Text Metadata</h4>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(text.metadata).map(([key, value]) => (
                <div key={key} className="metadata-item">
                  <span className="font-medium">{key}:</span>{' '}
                  <span className="text-base-content/70">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Text Divisions */}
      <div className="divisions-container space-y-4">
        {text.divisions?.map(renderDivision)}
      </div>
    </div>
  )
}
