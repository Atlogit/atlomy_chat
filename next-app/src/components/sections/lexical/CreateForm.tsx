'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue, CreateResponse, TaskStatus, BatchCreateResponse, LemmaCreate } from '../../../utils/api'

interface Citation {
  sentence: {
    id: string;
    text: string;
    prev_sentence?: string;
    next_sentence?: string;
    tokens?: Record<string, any>;
  };
  citation: string;
  context: {
    line_id: string;
    line_text: string;
    line_numbers: number[];
  };
  location: {
    volume?: string;
    chapter?: string;
    section?: string;
  };
  source: {
    author: string;
    work: string;
  };
}

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
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [showCitationModal, setShowCitationModal] = useState(false)
  const [versions, setVersions] = useState<string[]>([])
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  
  const createApi = useApi<CreateResponse>()
  const batchCreateApi = useApi<BatchCreateResponse>()
  const statusApi = useApi<TaskStatus>()
  const versionsApi = useApi<{ versions: string[] }>()

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

              // Load versions if entry was created/updated successfully
              if (status.status === 'completed' && status.entry) {
                loadVersions(status.entry.lemma)
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
   * Loads available versions for a lemma
   */
  const loadVersions = async (lemma: string) => {
    try {
      const result = await versionsApi.execute(API.lexical.versions(lemma), { method: 'GET' })
      if (result) {
        setVersions(result.versions)
      }
    } catch (err) {
      console.error('Error loading versions:', err)
    }
  }

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

  /**
   * Formats a citation for display
   */
  const formatCitation = (citation: Citation) => {
    const authorWork = `${citation.source.author}, ${citation.source.work}`
    const location = [
      citation.location.volume && `Volume ${citation.location.volume}`,
      citation.location.chapter && `Chapter ${citation.location.chapter}`,
      citation.location.section && `Section ${citation.location.section}`
    ].filter(Boolean).join(', ')
    
    return `${authorWork} (${location})`
  }

  /**
   * Renders a citation with context preview
   */
  const renderCitation = (citation: Citation) => (
    <div className="card bg-base-200 p-4 mb-4">
      <div className="flex justify-between items-start">
        <div className="font-medium">{formatCitation(citation)}</div>
        <Button
          onClick={() => {
            setSelectedCitation(citation)
            setShowCitationModal(true)
          }}
          variant="outline"
          className="btn-sm"
        >
          Show Context
        </Button>
      </div>
      <div className="mt-2 text-sm">
        {citation.sentence.text.length > 100 
          ? citation.sentence.text.substring(0, 100) + '...'
          : citation.sentence.text}
      </div>
    </div>
  )

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
              spellCheck={false}
              autoComplete="off"
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

          {/* Version Selection */}
          {versions.length > 0 && (
            <div className="form-control">
              <label className="label">
                <span className="label-text">Version</span>
              </label>
              <select
                className="select select-bordered"
                value={selectedVersion || ''}
                onChange={(e) => setSelectedVersion(e.target.value || null)}
              >
                <option value="">Latest Version</option>
                {versions.map((version) => (
                  <option key={version} value={version}>
                    Version {version}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Results Display with Enhanced Citations */}
          {taskStatus?.entry && (
            <div className="card bg-base-100 shadow-lg">
              <div className="card-body">
                <h2 className="card-title">{taskStatus.entry.lemma}</h2>
                <p className="text-lg">{taskStatus.entry.translation}</p>
                
                <div className="divider">Description</div>
                <p>{taskStatus.entry.short_description}</p>
                <p className="mt-2">{taskStatus.entry.long_description}</p>
                
                <div className="divider">Citations</div>
                <div className="space-y-4">
                  {taskStatus.entry.citations_used?.map((citation: Citation, index: number) => (
                    renderCitation(citation)
                  ))}
                </div>
                
                <div className="divider">Related Terms</div>
                <div className="flex flex-wrap gap-2">
                  {taskStatus.entry.related_terms?.map((term: string, index: number) => (
                    <div key={index} className="badge badge-primary">{term}</div>
                  ))}
                </div>
                
                <div className="divider">Version Info</div>
                <div className="text-sm">
                  <p>Created: {new Date(taskStatus.entry.created_at).toLocaleString()}</p>
                  <p>Updated: {new Date(taskStatus.entry.updated_at).toLocaleString()}</p>
                  <p>Version: {taskStatus.entry.version}</p>
                </div>
              </div>
            </div>
          )}

          {taskStatus?.status === 'error' && (
            <div className="alert alert-error">
              <p>{taskStatus.message}</p>
            </div>
          )}

          {taskStatus?.status === 'in_progress' && (
            <div className="alert alert-info">
              <p>{taskStatus.message}</p>
              {retryCount > 0 && <p>Retrying... (Attempt {retryCount})</p>}
            </div>
          )}
        </>
      )}

      {/* Citation Context Modal */}
      {showCitationModal && selectedCitation && (
        <dialog className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Citation Context</h3>
            <div className="py-4">
              {selectedCitation.sentence.prev_sentence && (
                <p className="text-sm opacity-70">{selectedCitation.sentence.prev_sentence}</p>
              )}
              <p className="font-medium my-2">{selectedCitation.sentence.text}</p>
              {selectedCitation.sentence.next_sentence && (
                <p className="text-sm opacity-70">{selectedCitation.sentence.next_sentence}</p>
              )}
            </div>
            <div className="modal-action">
              <Button onClick={() => setShowCitationModal(false)}>Close</Button>
            </div>
          </div>
        </dialog>
      )}
    </div>
  )
}
