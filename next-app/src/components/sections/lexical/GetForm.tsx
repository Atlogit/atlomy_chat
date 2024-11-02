'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue } from '../../../utils/api'

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
  const { execute: executeDelete, isLoading: isDeleting } = useApi()

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

  /**
   * Handles the deletion of a lexical value.
   * 
   * @async
   * @function
   */
  const handleDelete = async () => {
    if (!lemma.trim()) return
    
    await executeDelete(API.lexical.delete(lemma.trim()))
    setLemma('')
  }

  return (
    <div className="form-control gap-4">
      <div className="flex flex-col gap-4">
        <div>
          <label className="label">
            <span className="label-text">Lemma</span>
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              className="input input-bordered flex-grow"
              placeholder="Enter lemma to retrieve..."
              value={lemma}
              onChange={(e) => setLemma(e.target.value)}
            />
            <div className="flex gap-2">
              <Button
                onClick={handleSubmit}
                isLoading={isLoading}
                disabled={!lemma.trim()}
              >
                Get Lexical Value
              </Button>
              <Button
                onClick={handleDelete}
                isLoading={isDeleting}
                disabled={!lemma.trim()}
                className="btn-error"
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      </div>

      <ResultsDisplay
        title="Lexical Value"
        content={error ? null : data}
        error={error ? error.message : null}
      />
    </div>
  )
}
