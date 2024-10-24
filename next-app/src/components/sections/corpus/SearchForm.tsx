'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { ResultsDisplay } from '@/components/ui/ResultsDisplay'
import { useLoading } from '@/hooks/useLoading'
import { fetchApi, API, TextSearchRequest } from '@/utils/api'

interface SearchResult {
  textId: string
  title: string
  matches: Array<{
    context: string
    line: number
  }>
}

interface SearchFormProps {
  onResultSelect: (textId: string) => void
}

export function SearchForm({ onResultSelect }: SearchFormProps) {
  const [query, setQuery] = useState('')
  const [searchLemma, setSearchLemma] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const { isLoading, error, execute } = useLoading<SearchResult[]>()

  const handleSubmit = async () => {
    if (!query.trim()) return

    const request: TextSearchRequest = {
      query: query.trim(),
      searchLemma
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
          />
        </div>

        <div className="form-control">
          <label className="label cursor-pointer">
            <span className="label-text">Search by lemma</span>
            <input
              type="checkbox"
              className="checkbox"
              checked={searchLemma}
              onChange={(e) => setSearchLemma(e.target.checked)}
            />
          </label>
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
          {results.map((result) => (
            <div key={result.textId} className="card bg-base-200">
              <div className="card-body">
                <h3 className="card-title text-lg">{result.title}</h3>
                <div className="matches space-y-2">
                  {result.matches.map((match, index) => (
                    <div key={index} className="match bg-base-300 p-3 rounded">
                      <p className="text-sm">{match.context}</p>
                      <div className="text-xs text-base-content/70 mt-1">
                        Line: {match.line}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="card-actions justify-end mt-4">
                  <Button
                    onClick={() => onResultSelect(result.textId)}
                    variant="outline"
                  >
                    View Full Text
                  </Button>
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
