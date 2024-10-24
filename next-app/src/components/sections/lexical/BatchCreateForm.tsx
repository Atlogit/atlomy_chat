'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay, ProgressDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalBatchCreateRequest } from '../../../utils/api'

/**
 * BatchCreateForm Component
 * 
 * This component provides a form for batch creation of lexical values.
 * It allows users to input multiple words, optionally search for lemma forms,
 * and submit the data to create multiple lexical entries at once.
 *
 * @component
 */
export function BatchCreateForm() {
  const [words, setWords] = useState('')
  const [searchLemma, setSearchLemma] = useState(false)
  const { data, error, isLoading, progress, execute } = useApi<any>() // Use appropriate type instead of 'any'

  /**
   * Handles the form submission to create multiple lexical values in batch.
   * 
   * @async
   * @function
   */
  const handleSubmit = async () => {
    const wordList = words
      .split('\n')
      .map(word => word.trim())
      .filter(word => word.length > 0)

    if (wordList.length === 0) return

    const request: LexicalBatchCreateRequest = {
      words: wordList,
      searchLemma
    }

    await execute(API.lexical.batchCreate, {
      method: 'POST',
      body: JSON.stringify(request),
    })

    // Clear form after successful submission
    if (data) {
      setWords('')
    }
  }

  return (
    <div className="form-control gap-4">
      <div>
        <label className="label">
          <span className="label-text">Words (one per line)</span>
        </label>
        <textarea
          className="textarea textarea-bordered w-full h-32"
          placeholder="Enter words to create lexical values for..."
          value={words}
          onChange={(e) => setWords(e.target.value)}
        />
      </div>

      <div className="form-control">
        <label className="label cursor-pointer">
          <span className="label-text">Search for lemma forms</span>
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
        disabled={!words.trim()}
      >
        Create Lexical Values
      </Button>

      {isLoading && (
        <ProgressDisplay
          current={progress.current}
          total={progress.total}
        />
      )}

      <ResultsDisplay
        title="Batch Creation Results"
        content={error ? null : data ? `Successfully processed ${data.length} words.` : null}
        error={error ? error.message : null}
      />
    </div>
  )
}
