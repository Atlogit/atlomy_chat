'use client'

import { useState, useEffect, useMemo } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, AnalysisRequest, AnalysisResponse, TokenCountResponse } from '../../../utils/api'

interface Context {
  text: string;
  author?: string;
  reference?: string;
}

/**
 * LLMSection Component
 * 
 * This component represents the LLM (Language Model) Assistant section of the application.
 * It provides an interface for analyzing terms using context from the corpus.
 * 
 * @component
 */
export function LLMSection() {
  const [term, setTerm] = useState('')
  const [contexts, setContexts] = useState<Context[]>([])
  const [response, setResponse] = useState('')
  const [tokenCount, setTokenCount] = useState<TokenCountResponse | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [processingStage, setProcessingStage] = useState<string | null>(null)
  const { data, error, isLoading = false, execute } = useApi<AnalysisResponse>()

  useEffect(() => {
    if (data) {
      handleApiResponse(data)
    }
  }, [data])

  /**
   * Checks the token count for the current term and contexts
   */
  const checkTokenCount = async () => {
    if (!term || contexts.length === 0) return

    const request: AnalysisRequest = {
      term,
      contexts,
      stream: false
    }

    try {
      const response = await fetch(API.llm.tokenCount, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      })

      if (!response.ok) throw new Error('Failed to get token count')

      const tokenData: TokenCountResponse = await response.json()
      setTokenCount(tokenData)
    } catch (error) {
      console.error('Error checking token count:', error)
    }
  }

  /**
   * Handles the submission of the term analysis request
   */
  const handleSubmit = async () => {
    if (!term.trim() || contexts.length === 0) return

    setProcessingStage('Initializing analysis...')
    setResponse('')

    const request: AnalysisRequest = {
      term,
      contexts,
      stream: isStreaming
    }

    if (isStreaming) {
      await handleStreamingAnalysis(request)
    } else {
      await execute(API.llm.analyze, {
        method: 'POST',
        body: JSON.stringify(request),
      })
    }
  }

  /**
   * Handles streaming analysis responses
   */
  const handleStreamingAnalysis = async (request: AnalysisRequest) => {
    try {
      const response = await fetch(API.llm.analyzeStream, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      })

      if (!response.ok) throw new Error('Streaming request failed')
      
      const reader = response.body?.getReader()
      if (!reader) throw new Error('Failed to get response reader')

      setResponse('')
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Decode and handle the chunk
        const chunk = new TextDecoder().decode(value)
        setResponse(prev => prev + chunk)
      }

      setProcessingStage(null)
    } catch (error) {
      console.error('Streaming error:', error)
      setResponse('Error during streaming analysis')
      setProcessingStage(null)
    }
  }

  const handleApiResponse = (result: AnalysisResponse) => {
    setResponse(result.text)
    setProcessingStage(null)
  }

  /**
   * Adds a new context for analysis
   */
  const addContext = () => {
    setContexts([...contexts, { text: '', author: '', reference: '' }])
  }

  /**
   * Updates a context at the specified index
   */
  const updateContext = (index: number, field: keyof Context, value: string) => {
    const newContexts = [...contexts]
    newContexts[index] = { ...newContexts[index], [field]: value }
    setContexts(newContexts)
    checkTokenCount()
  }

  /**
   * Removes a context at the specified index
   */
  const removeContext = (index: number) => {
    setContexts(contexts.filter((_, i) => i !== index))
    checkTokenCount()
  }

  // Compute submission button disabled state
  const isSubmitDisabled = useMemo(() => {
    return !term.trim() || 
           contexts.length === 0 || 
           (tokenCount ? !tokenCount.within_limits : false)
  }, [term, contexts, tokenCount])

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">Term Analysis</h2>
        
        {/* Term Input */}
        <div className="form-control">
          <label className="label">
            <span className="label-text">Term to Analyze</span>
          </label>
          <input
            type="text"
            className="input input-bordered"
            value={term}
            onChange={(e) => {
              setTerm(e.target.value)
              checkTokenCount()
            }}
            placeholder="Enter a term..."
            spellCheck={false}
            autoComplete="off"
          />
        </div>

        {/* Contexts Section */}
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <label className="label-text">Contexts</label>
            <Button onClick={addContext} variant="outline" className="btn-sm">
              Add Context
            </Button>
          </div>
          
          {contexts.map((context, index) => (
            <div key={index} className="card bg-base-200 p-4 mb-4">
              <div className="flex justify-between items-start">
                <span className="font-medium">Context {index + 1}</span>
                <Button
                  onClick={() => removeContext(index)}
                  variant="outline"
                  className="btn-sm text-error"
                >
                  Remove
                </Button>
              </div>
              
              <div className="space-y-4 mt-2">
                <textarea
                  className="textarea textarea-bordered w-full"
                  value={context.text}
                  onChange={(e) => updateContext(index, 'text', e.target.value)}
                  placeholder="Enter context text..."
                  rows={3}
                  spellCheck={false}
                  autoComplete="off"
                />
                
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    className="input input-bordered"
                    value={context.author || ''}
                    onChange={(e) => updateContext(index, 'author', e.target.value)}
                    placeholder="Author (optional)"
                    spellCheck={false}
                    autoComplete="off"
                  />
                  <input
                    type="text"
                    className="input input-bordered"
                    value={context.reference || ''}
                    onChange={(e) => updateContext(index, 'reference', e.target.value)}
                    placeholder="Reference (optional)"
                    spellCheck={false}
                    autoComplete="off"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Token Count Display */}
        {tokenCount && (
          <div className={`alert ${tokenCount.within_limits ? 'alert-success' : 'alert-warning'} mt-4`}>
            <div className="flex justify-between items-center w-full">
              <span>Tokens: {tokenCount.count}</span>
              <span>{tokenCount.within_limits ? 'Within limits' : 'Exceeds limits'}</span>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex gap-4 mt-4">
          <div className="form-control">
            <label className="label cursor-pointer">
              <span className="label-text mr-2">Stream Response</span>
              <input
                type="checkbox"
                className="toggle"
                checked={isStreaming}
                onChange={(e) => setIsStreaming(e.target.checked)}
              />
            </label>
          </div>
          
          <Button
            onClick={handleSubmit}
            isLoading={isLoading}
            disabled={isSubmitDisabled}
            className="flex-1"
          >
            Analyze Term
          </Button>
        </div>

        {/* Processing Status */}
        {(isLoading || processingStage) && (
          <div className="mt-4 flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mr-2"></div>
            <span>{processingStage || 'Processing...'}</span>
          </div>
        )}

        {/* Results Display */}
        <ResultsDisplay
          title="Analysis Results"
          content={error ? null : response}
          error={error ? error.message : undefined}
        />
      </div>
    </div>
  )
}
