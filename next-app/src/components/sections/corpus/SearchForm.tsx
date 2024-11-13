'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useLoading } from '../../../hooks/useLoading'
import { fetchApi, API, TextSearchRequest, Citation, CitationObject, TokenInfo } from '../../../utils/api'

interface SearchFormProps {
  onResultSelect: (textId: string) => void
}

export function SearchForm({ onResultSelect }: SearchFormProps) {
  const [query, setQuery] = useState('')
  const [searchLemma, setSearchLemma] = useState(false)
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [results, setResults] = useState<CitationObject[]>([])
  const { isLoading, error, execute } = useLoading<CitationObject[]>()

  // Categories for ancient medical texts
  const availableCategories = [
    'Body Part',
    'Adjectives/Qualities',
    'Topography',
    'Division',
    'Technical Appellation',
    'Action Verbs',
    'Pathology',
    'Physiology',
    'Medical',
    'Tools',
    'Symmetry/Opposition',
    'Colour'
  ]

  const handleSubmit = async () => {
    if (!query.trim()) return

    const request: TextSearchRequest = {
      query: query.trim(),
      search_lemma: searchLemma,
      categories: selectedCategories.length > 0 ? selectedCategories : undefined
    }

    const searchResults = await execute(
      fetchApi<CitationObject[]>(API.corpus.search, {
        method: 'POST',
        body: JSON.stringify(request)
      })
    )

    if (searchResults) {
      setResults(searchResults)
    }
  }

  const renderCitation = (result: CitationObject) => {
    const parts = []

    // Citation components from source
    if (result.source.author) parts.push(result.source.author)
    if (result.source.work) parts.push(result.source.work)

    // Structural components from location
    const structural = []
    if (result.location.volume) structural.push(`Vol. ${result.location.volume}`)
    if (result.location.chapter) structural.push(`Ch. ${result.location.chapter}`)
    if (result.location.section) structural.push(`§${result.location.section}`)
    
    if (structural.length > 0) {
      parts.push(structural.join(', '))
    }

    return parts.join(' ')
  }

  const renderSpacyTokens = (result: CitationObject) => {
    if (!result.sentence.tokens) return null

    // Filter interesting tokens
    const tokens = result.sentence.tokens.filter(token => 
      !token.is_stop && 
      (token.pos === 'NOUN' || token.pos === 'VERB' || token.pos === 'ADJ')
    )

    if (tokens.length === 0) return null

    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {tokens.map((token, index) => (
          <span 
            key={`${token.text}-${index}`}
            className="text-xs px-1 py-0.5 rounded bg-base-100"
            title={`POS: ${token.pos}, Lemma: ${token.lemma}`}
          >
            {token.text}
          </span>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="form-control gap-4">
        <div>
          <label className="label">
            <span className="label-text">Search Query</span>
          </label>
          <input
            type="text"
            className="input input-bordered w-full"
            placeholder="Enter search terms..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSubmit()
              }
            }}
          />
        </div>

        <div className="flex items-center gap-4">
          <div className="form-control">
            <label className="label cursor-pointer">
              <span className="label-text mr-2">Search by lemma</span>
              <input
                type="checkbox"
                className="checkbox"
                checked={searchLemma}
                onChange={(e) => setSearchLemma(e.target.checked)}
              />
            </label>
          </div>

          <div className="divider divider-horizontal"></div>

          <div className="form-control flex-1">
            <label className="label">
              <span className="label-text">Categories</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {availableCategories.map((category) => (
                <label
                  key={category}
                  className={`badge badge-outline cursor-pointer ${
                    selectedCategories.includes(category) ? 'badge-primary' : ''
                  }`}
                  onClick={() => {
                    setSelectedCategories((prev) =>
                      prev.includes(category)
                        ? prev.filter((c) => c !== category)
                        : [...prev, category]
                    )
                  }}
                >
                  {category}
                </label>
              ))}
            </div>
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          isLoading={isLoading}
          disabled={!query.trim()}
        >
          Search Texts
        </Button>
      </div>

      {error ? (
        <ResultsDisplay error={error} content={null} />
      ) : results.length > 0 ? (
        <div className="search-results space-y-6">
          {results.map((result, idx) => (
            <div key={`${result.context.line_id}-${idx}`} className="card bg-base-200">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="card-title text-lg">
                      {result.source.work}
                    </h3>
                    {result.source.author && (
                      <p className="text-base-content/70 text-sm">
                        by {result.source.author}
                      </p>
                    )}
                  </div>
                  <Button
                    onClick={() => onResultSelect(result.context.line_id.split('-')[0])}
                    variant="outline"
                    className="btn-sm"
                  >
                    View Full Text
                  </Button>
                </div>

                <div className="match bg-base-300 p-4 rounded">
                  {/* Citation and Line Info */}
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-sm font-mono bg-base-100 px-2 py-1 rounded">
                      {renderCitation(result)}
                    </span>
                    <span className="text-xs text-base-content/70">
                      Line {result.context.line_numbers[0]}
                    </span>
                  </div>

                  {/* Content */}
                  <p className="text-sm whitespace-pre-line">{result.sentence.text}</p>

                  {/* Context */}
                  {(result.sentence.prev_sentence || result.sentence.next_sentence) && (
                    <div className="mt-2 text-sm text-base-content/70">
                      {result.sentence.prev_sentence && (
                        <div className="mb-1">↑ {result.sentence.prev_sentence}</div>
                      )}
                      {result.sentence.next_sentence && (
                        <div className="mt-1">↓ {result.sentence.next_sentence}</div>
                      )}
                    </div>
                  )}

                  {/* spaCy Token Analysis */}
                  {renderSpacyTokens(result)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : query.trim() && !isLoading ? (
        <div className="text-center py-8">
          <p className="text-base-content/70">No results found</p>
        </div>
      ) : null}
    </div>
  )
}
