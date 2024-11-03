'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useLoading } from '../../../hooks/useLoading'
import { fetchApi, API, TextSearchRequest, SearchResult } from '../../../utils/api'

interface SearchFormProps {
  onResultSelect: (textId: string) => void
}

interface SpacyToken {
  text: string
  lemma_: string
  pos_: string
  tag_: string
  dep_: string
  is_stop: boolean
  has_vector: boolean
  vector_norm: number
  is_oov: boolean
}

export function SearchForm({ onResultSelect }: SearchFormProps) {
  const [query, setQuery] = useState('')
  const [searchLemma, setSearchLemma] = useState(false)
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [results, setResults] = useState<SearchResult[]>([])
  const { isLoading, error, execute } = useLoading<SearchResult[]>()

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
      fetchApi<SearchResult[]>(API.corpus.search, {
        method: 'POST',
        body: JSON.stringify(request)
      })
    )

    if (searchResults) {
      setResults(searchResults)
    }
  }

  const renderCitation = (result: SearchResult) => {
    const parts = []

    // Citation components based on actual returned fields
    if (result.author_name) parts.push(result.author_name)
    if (result.work_name) parts.push(result.work_name)

    // Structural components
    const structural = []
    if (result.volume) structural.push(`Vol. ${result.volume}`)
    if (result.chapter) structural.push(`Ch. ${result.chapter}`)
    if (result.section) structural.push(`§${result.section}`)
    
    if (structural.length > 0) {
      parts.push(structural.join(', '))
    }

    return parts.join(' ')
  }

  const renderSpacyTokens = (result: SearchResult) => {
    if (!result.spacy_data) return null

    // Extract interesting token attributes
    const tokens = Object.entries(result.spacy_data as Record<string, SpacyToken>)
      .filter(([_, token]) => 
        token.is_stop === false && 
        (token.pos_ === 'NOUN' || token.pos_ === 'VERB' || token.pos_ === 'ADJ')
      )

    if (tokens.length === 0) return null

    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {tokens.map(([word, token]) => (
          <span 
            key={word} 
            className="text-xs px-1 py-0.5 rounded bg-base-100"
            title={`POS: ${token.pos_}, Lemma: ${token.lemma_}`}
          >
            {word}
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
            <div key={`${result.text_id}-${idx}`} className="card bg-base-200">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="card-title text-lg">
                      {result.work_name}
                    </h3>
                    {result.author_name && (
                      <p className="text-base-content/70 text-sm">
                        by {result.author_name}
                      </p>
                    )}
                  </div>
                  <Button
                    onClick={() => onResultSelect(result.text_id)}
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
                      Line {result.min_line_number}
                    </span>
                  </div>

                  {/* Content */}
                  <p className="text-sm whitespace-pre-line">{result.sentence_text}</p>

                  {/* Categories */}
                  {result.categories && result.categories.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      {result.categories.map((category) => (
                        <span
                          key={category}
                          className="badge badge-sm badge-ghost"
                        >
                          {category}
                        </span>
                      ))}
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
