'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue, formatResults } from '../../../utils/api'

/**
 * GetForm Component
 * 
 * This component provides a form for retrieving lexical values.
 * It allows users to input a lemma and fetch its corresponding lexical value.
 *
 * @component
 */
export function GetForm() {
  const [lemma, setLemma] = useState('')
  const { data, error, isLoading, execute } = useApi<LexicalValue>()

  /**
   * Handles the form submission to retrieve a lexical value.
   * 
   * @async
   * @function
   */
  const handleSubmit = async () => {
    if (!lemma.trim()) return

    await execute(API.lexical.get(lemma.trim()))

    // Clear input after submission
    if (data) {
      setLemma('')
    }
  }

  return (
    <div className="form-control gap-4">
      <div>
        <label className="label">
          <span className="label-text">Lemma</span>
        </label>
        <input
          type="text"
          className="input input-bordered w-full"
          placeholder="Enter lemma to retrieve..."
          value={lemma}
          onChange={(e) => setLemma(e.target.value)}
        />
      </div>

      <Button
        onClick={handleSubmit}
        isLoading={isLoading}
        disabled={!lemma.trim()}
      >
        Get Lexical Value
      </Button>

      <ResultsDisplay
        title="Lexical Value"
        content={error ? null : data ? formatResults(data) : null}
        error={error ? error.message : null}
      />
    </div>
  )
}
