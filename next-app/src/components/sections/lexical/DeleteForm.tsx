'use client'

import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue, DeleteTriggerResponse } from '../../../utils/api'

/**
 * DeleteForm Component
 * 
 * This component provides a form for deleting lexical values.
 * It allows users to search for a lemma, view its details, and confirm deletion.
 *
 * @component
 */
export function DeleteForm() {
  const [lemma, setLemma] = useState('')
  const [valueToDelete, setValueToDelete] = useState<LexicalValue | null>(null)
  const [triggerId, setTriggerId] = useState<string | null>(null)
  const { data: searchData, error: searchError, isLoading: isSearching, execute: executeSearch } = useApi<LexicalValue>()
  const { data: triggerData, error: triggerError, isLoading: isTriggering, execute: executeTrigger } = useApi<DeleteTriggerResponse>()
  const { data: deleteData, error: deleteError, isLoading: isDeleting, execute: executeDelete } = useApi<void>()

  /**
   * Handles the search operation to fetch the lexical value to be deleted.
   * 
   * @async
   * @function
   */
  const handleSearch = async () => {
    if (!lemma.trim()) return

    await executeSearch(API.lexical.get(lemma.trim()))

    if (searchData) {
      setValueToDelete(searchData)
      // Reset trigger when searching for a new value
      setTriggerId(null)
    }
  }

  /**
   * Handles triggering the delete operation.
   * 
   * @async
   * @function
   */
  const handleTriggerDelete = async () => {
    if (!lemma.trim() || !valueToDelete) return

    const result = await executeTrigger(API.lexical.deleteTrigger(lemma.trim()), {
      method: 'POST'
    })

    if (result?.trigger_id) {
      setTriggerId(result.trigger_id)
    }
  }

  /**
   * Handles the delete operation to remove the lexical value.
   * 
   * @async
   * @function
   */
  const handleDelete = async () => {
    if (!lemma.trim() || !valueToDelete || !triggerId) return

    await executeDelete(`${API.lexical.delete(lemma.trim())}?trigger_id=${triggerId}`, {
      method: 'DELETE'
    })

    // Clear form after successful deletion
    if (deleteData !== undefined) {
      setLemma('')
      setValueToDelete(null)
      setTriggerId(null)
    }
  }

  const isLoading = isSearching || isTriggering || isDeleting
  const error = searchError || triggerError || deleteError

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
              placeholder="Enter lemma to delete..."
              value={lemma}
              onChange={(e) => setLemma(e.target.value)}
            />
            <div className="flex gap-2">
              <Button
                onClick={handleSearch}
                isLoading={isSearching}
                disabled={!lemma.trim()}
                variant="outline"
              >
                Search
              </Button>
              {valueToDelete && !triggerId && (
                <Button
                  onClick={handleTriggerDelete}
                  isLoading={isTriggering}
                  variant="outline"
                  className="btn-warning"
                >
                  Confirm
                </Button>
              )}
              {valueToDelete && triggerId && (
                <Button
                  onClick={handleDelete}
                  isLoading={isDeleting}
                  variant="error"
                >
                  Delete
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {valueToDelete && (
        <div className={`alert ${triggerId ? 'alert-error' : 'alert-warning'}`}>
          <div>
            <h3 className="font-bold">{triggerId ? 'Final Confirmation' : 'Confirm Deletion'}</h3>
            <p>{triggerId ? 'This action cannot be undone. Are you absolutely sure?' : 'Are you sure you want to delete this lexical value?'}</p>
            <pre className="mt-2 p-2 bg-base-200 rounded">
              {JSON.stringify(valueToDelete, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <ResultsDisplay
        title="Delete Result"
        content={error ? null : deleteData !== undefined ? `Successfully deleted: ${lemma}` : null}
        error={error ? error.message : null}
      />
    </div>
  )
}
