'use client'

import { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue, CreateResponse, TaskStatus } from '../../../utils/api'

/**
 * CreateForm Component
 * 
 * This component provides a form for creating new lexical values.
 * It allows users to input a lemma, then submit the data to create
 * a new lexical entry. If the lemma already exists, it proposes an update.
 *
 * @component
 */
export function CreateForm() {
  const [lemma, setLemma] = useState('')
  const [showUpdateConfirmation, setShowUpdateConfirmation] = useState(false)
  const [existingEntry, setExistingEntry] = useState<LexicalValue | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  
  const createApi = useApi<CreateResponse>()
  const statusApi = useApi<TaskStatus>()

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (taskId) {
      intervalId = setInterval(async () => {
        try {
          const status = await statusApi.execute(API.lexical.status(taskId), { method: 'GET' })
          if (status) {
            setTaskStatus(status)

            if (status.status === 'completed' || status.status === 'error') {
              if (intervalId) clearInterval(intervalId)
              setTaskId(null)
              setRetryCount(0)
            }
          }
        } catch (err) {
          console.error('Error checking task status:', err)
          setRetryCount(prevCount => prevCount + 1)
          if (retryCount >= 3) {
            if (intervalId) clearInterval(intervalId)
            setTaskId(null)
            setTaskStatus({ status: 'error', message: 'Failed to check task status after multiple attempts' })
            setRetryCount(0)
          }
        }
      }, 2000) // Check every 2 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [taskId, statusApi, retryCount])

  /**
   * Handles the form submission to create a new lexical value.
   * 
   * @async
   * @function
   */
  const handleSubmit = async () => {
    if (!lemma.trim()) return

    try {
      console.log('Submitting form with data:', { lemma })
      const result = await createApi.execute(API.lexical.create, {
        method: 'POST',
        body: JSON.stringify({
          lemma: lemma.trim(),
          searchLemma: true
        })
      })

      console.log('API Response:', result)

      if (result && result.task_id) {
        setTaskId(result.task_id)
        setTaskStatus({ status: 'in_progress', message: 'Creating lexical value...' })
      } else {
        console.error('API returned unexpected result')
        setTaskStatus({ status: 'error', message: 'Unexpected API response' })
      }
    } catch (err) {
      console.error('Error in handleSubmit:', err)
      if (err instanceof Error) {
        console.error('Error details:', err.message, err.stack)
      }
      setTaskStatus({ status: 'error', message: `Failed to create lexical entry: ${err instanceof Error ? err.message : 'Unknown error'}` })
    }
  }

  /**
   * Handles the update confirmation when a lemma already exists.
   * 
   * @function
   */
  const handleUpdateConfirmation = (confirm: boolean) => {
    setShowUpdateConfirmation(false)
    if (confirm) {
      console.log('Update confirmed')
      // Here you might want to navigate to an update form or open a modal
      // for updating the existing entry
    } else {
      console.log('Update cancelled')
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
          placeholder="Enter lemma..."
          value={lemma}
          onChange={(e) => setLemma(e.target.value)}
        />
      </div>

      <Button
        onClick={handleSubmit}
        isLoading={createApi.isLoading || statusApi.isLoading || (taskStatus?.status === 'in_progress')}
        disabled={!lemma.trim() || (taskStatus?.status === 'in_progress')}
      >
        Create Lexical Value
      </Button>

      {showUpdateConfirmation && (
        <div className="alert alert-warning">
          <p>This lemma already exists. Do you want to update it?</p>
          <div className="flex gap-2 mt-2">
            <Button onClick={() => handleUpdateConfirmation(true)} className="btn-sm">
              Yes, Update
            </Button>
            <Button onClick={() => handleUpdateConfirmation(false)} className="btn-sm btn-outline">
              No, Cancel
            </Button>
          </div>
        </div>
      )}

      <ResultsDisplay
        title={taskStatus?.action === 'update' ? "Existing Lexical Value" : "Created Lexical Value"}
        content={taskStatus?.status === 'error' ? `Error: ${taskStatus.message}` : taskStatus?.entry ? JSON.stringify(taskStatus.entry, null, 2) : null}
        error={taskStatus?.status === 'error' ? taskStatus.message : null}
      />

      {taskStatus?.status === 'in_progress' && (
        <div className="alert alert-info">
          <p>{taskStatus.message}</p>
          {retryCount > 0 && <p>Retrying... (Attempt {retryCount})</p>}
        </div>
      )}
    </div>
  )
}
