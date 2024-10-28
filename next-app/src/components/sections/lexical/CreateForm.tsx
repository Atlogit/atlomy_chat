'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue, CreateResponse, TaskStatus, BatchCreateResponse, LemmaCreate } from '../../../utils/api'

/**
 * CreateForm Component
 * 
 * This component provides a form for creating new lexical values.
 * It supports both single and batch creation of lemmas.
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
  const [batchMode, setBatchMode] = useState(false)
  const [batchFile, setBatchFile] = useState<File | null>(null)
  const [batchProgress, setBatchProgress] = useState<BatchCreateResponse | null>(null)
  
  const createApi = useApi<CreateResponse>()
  const batchCreateApi = useApi<BatchCreateResponse>()
  const statusApi = useApi<TaskStatus>()

  // Task status polling
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

              // If it's an update action, show the update confirmation
              if (status.status === 'completed' && status.action === 'update') {
                setExistingEntry(status.entry || null)
                setShowUpdateConfirmation(true)
              }
            }
          }
        } catch (err) {
          console.error('Error checking task status:', err)
          setRetryCount(prevCount => prevCount + 1)
          if (retryCount >= 3) {
            if (intervalId) clearInterval(intervalId)
            setTaskId(null)
            setTaskStatus({ 
              status: 'error', 
              message: 'Failed to check task status after multiple attempts' 
            })
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
        setTaskStatus({ 
          status: 'in_progress', 
          message: 'Creating lexical value...' 
        })
      } else {
        console.error('API returned unexpected result')
        setTaskStatus({ 
          status: 'error', 
          message: 'Unexpected API response' 
        })
      }
    } catch (err) {
      console.error('Error in handleSubmit:', err)
      if (err instanceof Error) {
        console.error('Error details:', err.message, err.stack)
      }
      setTaskStatus({ 
        status: 'error', 
        message: `Failed to create lexical entry: ${err instanceof Error ? err.message : 'Unknown error'}` 
      })
    }
  }

  /**
   * Handles batch file upload and processing.
   */
  const handleBatchUpload = async (file: File) => {
    try {
      const text = await file.text()
      const lemmas: LemmaCreate[] = text.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(lemma => ({
          lemma,
          searchLemma: true
        }))

      const result = await batchCreateApi.execute(API.lexical.batchCreate, {
        method: 'POST',
        body: JSON.stringify({ lemmas })
      })

      setBatchProgress(result)
    } catch (err) {
      console.error('Error in batch upload:', err)
      setBatchProgress({
        successful: [],
        failed: [{
          lemma: 'Batch Upload',
          error: err instanceof Error ? err.message : 'Unknown error'
        }],
        total: 0
      })
    }
  }

  /**
   * Handles the update confirmation when a lemma already exists.
   */
  const handleUpdateConfirmation = async (confirm: boolean) => {
    setShowUpdateConfirmation(false)
    if (confirm && existingEntry) {
      try {
        console.log('Updating existing entry:', existingEntry)
        const result = await createApi.execute(API.lexical.update, {
          method: 'PUT',
          body: JSON.stringify({
            lemma: existingEntry.lemma,
            // Add any update fields here
          })
        })

        if (result && result.task_id) {
          setTaskId(result.task_id)
          setTaskStatus({ 
            status: 'in_progress', 
            message: 'Updating lexical value...' 
          })
        }
      } catch (err) {
        console.error('Error in handleUpdateConfirmation:', err)
        setTaskStatus({ 
          status: 'error', 
          message: `Failed to update lexical entry: ${err instanceof Error ? err.message : 'Unknown error'}` 
        })
      }
    }
  }

  return (
    <div className="form-control gap-4">
      {/* Mode Toggle */}
      <div className="flex justify-end mb-4">
        <button
          className={`btn btn-sm ${batchMode ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setBatchMode(!batchMode)}
        >
          {batchMode ? 'Switch to Single Mode' : 'Switch to Batch Mode'}
        </button>
      </div>

      {batchMode ? (
        /* Batch Upload Form */
        <div className="form-control gap-4">
          <div className="flex flex-col gap-2">
            <label className="label">
              <span className="label-text">Upload Lemmas File</span>
            </label>
            <input
              type="file"
              className="file-input file-input-bordered w-full"
              accept=".txt"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  setBatchFile(file)
                  handleBatchUpload(file)
                }
              }}
            />
            <p className="text-sm text-gray-500">
              Upload a text file with one lemma per line
            </p>
          </div>

          {batchProgress && (
            <div className="mt-4">
              <h3 className="text-lg font-semibold mb-2">Batch Processing Results</h3>
              <div className="stats shadow">
                <div className="stat">
                  <div className="stat-title">Total</div>
                  <div className="stat-value">{batchProgress.total}</div>
                </div>
                <div className="stat">
                  <div className="stat-title">Successful</div>
                  <div className="stat-value text-success">{batchProgress.successful.length}</div>
                </div>
                <div className="stat">
                  <div className="stat-title">Failed</div>
                  <div className="stat-value text-error">{batchProgress.failed.length}</div>
                </div>
              </div>

              {batchProgress.failed.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">Failed Entries</h4>
                  <div className="overflow-x-auto">
                    <table className="table table-compact w-full">
                      <thead>
                        <tr>
                          <th>Lemma</th>
                          <th>Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batchProgress.failed.map((failure, index) => (
                          <tr key={index}>
                            <td>{failure.lemma}</td>
                            <td className="text-error">{failure.error}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Single Entry Form */
        <>
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
        </>
      )}
    </div>
  )
}
