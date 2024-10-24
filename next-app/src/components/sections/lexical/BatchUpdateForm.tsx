'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay, ProgressDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalBatchUpdateRequest } from '../../../utils/api'

/**
 * BatchUpdateForm Component
 * 
 * This component provides a form for batch updating of lexical values.
 * It allows users to input multiple lemma-translation pairs and update them all at once.
 *
 * @component
 */
export function BatchUpdateForm() {
  const [updates, setUpdates] = useState('')
  const { data, error, isLoading, progress, execute } = useApi<any>() // Use appropriate type instead of 'any'

  /**
   * Handles the form submission to update multiple lexical values in batch.
   * 
   * @async
   * @function
   */
  const handleSubmit = async () => {
    // Parse the updates from textarea
    // Format expected: lemma: translation (one per line)
    const updateList = updates
      .split('\n')
      .map(line => {
        const [lemma, ...translationParts] = line.split(':')
        const translation = translationParts.join(':').trim()
        return {
          lemma: lemma.trim(),
          translation: translation
        }
      })
      .filter(update => update.lemma && update.translation)

    if (updateList.length === 0) return

    const request: LexicalBatchUpdateRequest = {
      updates: updateList
    }

    await execute(API.lexical.batchUpdate, {
      method: 'PUT',
      body: JSON.stringify(request),
    })

    // Clear form after successful submission
    if (data) {
      setUpdates('')
    }
  }

  return (
    <div className="form-control gap-4">
      <div>
        <label className="label">
          <span className="label-text">Updates (one per line, format: lemma: translation)</span>
        </label>
        <textarea
          className="textarea textarea-bordered w-full h-32"
          placeholder="Enter updates in format: lemma: translation&#10;Example:&#10;word: new translation&#10;another: updated meaning"
          value={updates}
          onChange={(e) => setUpdates(e.target.value)}
        />
      </div>

      <Button
        onClick={handleSubmit}
        isLoading={isLoading}
        disabled={!updates.trim()}
      >
        Update Lexical Values
      </Button>

      {isLoading && (
        <ProgressDisplay
          current={progress.current}
          total={progress.total}
        />
      )}

      <ResultsDisplay
        title="Batch Update Results"
        content={error ? null : data ? `Successfully updated ${data.length} lexical values.` : null}
        error={error ? error.message : null}
      />
    </div>
  )
}
