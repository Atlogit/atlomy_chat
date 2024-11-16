'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue, CreateResponse, TaskStatus, LemmaCreate } from '../../../utils/api'

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
  const [selectedCitation, setSelectedCitation] = useState<Citation | string | null>(null)
  const [showCitationModal, setShowCitationModal] = useState(false)
  
  const createApi = useApi<CreateResponse>()
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
        message: err instanceof Error ? err.message : 'An unknown error occurred',
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
          message: err instanceof Error ? err.message : 'An unknown error occurred',
        })
      }
    }
  }

  /**
   * Formats a citation for display
   */
  const formatCitation = (citation: Citation | string) => {
    if (typeof citation === 'string') {
    // For string citations (from LLM analysis), return as is
    return citation
    }

    // For full citation objects, format with all details
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
  const renderCitation = (citation: Citation | string) => {
    if (typeof citation === 'string') {
      // For string citations (from LLM analysis)
      return (
        <div key={citation} className="card bg-base-200 p-4 mb-4">
          <div className="text-sm">{citation}</div>
        </div>
      )
    }
    // For full citation objects
    return (
      <div key={citation.sentence.id} className="card bg-base-200 p-4 mb-4">
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
  }

  /**
   * Renders error details in a structured way
   */
  const renderError = (error: any) => {
    if (!error) return null;

    return (
      <div className="alert alert-error">
        <div className="flex flex-col gap-2">
          <p className="font-semibold">{error.message}</p>
          {error.detail && (
            <div className="text-sm mt-2 bg-base-300 p-2 rounded overflow-auto">
              <pre className="whitespace-pre-wrap">{error.detail}</pre>
            </div>
          )}
        </div>
      </div>
    );
  };

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

      {/* Error Display */}
      {(createApi.error || statusApi.error) && (
        <div className="mt-4">
          {createApi.error && renderError(createApi.error)}
          {statusApi.error && renderError(statusApi.error)}
        </div>
      )}

      {/* Results Display with Enhanced Citations */}
      {taskStatus?.entry && (
        <div className="card bg-base-100 shadow-lg">
          <div className="card-body">
            <h2 className="card-title">{taskStatus.entry.lemma}</h2>
            <p className="text-lg">{taskStatus.entry.translation}</p>
            
            <div className="divider">Short Description</div>
            <p>{taskStatus.entry.short_description}</p>
            
            <div className="divider">Long Description</div>
            <p>{taskStatus.entry.long_description}</p>
            
            <div className="divider">Related Terms</div>
            <div className="flex flex-wrap gap-2">
              {taskStatus.entry.related_terms?.map((term: string, index: number) => (
                <div key={`${term}-${index}`} className="badge badge-primary">{term}</div>
              ))}
            </div>
            
            <div className="divider">Citations Used</div>
            <div className="space-y-4">
              {taskStatus.entry.citations_used?.map((citation: Citation | string, index: number) => (
                <div key={index}>
                  {renderCitation(citation)}
                </div>
              ))}
            </div>

            <div className="divider">References</div>
            <div className="space-y-4">
              {taskStatus.entry.references?.citations?.map((citation: Citation, index: number) => (
                <div key={index}>
                  {renderCitation(citation)}
                </div>
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

      {/* Citation Context Modal */}
      {showCitationModal && selectedCitation && typeof selectedCitation !== 'string' && (
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
