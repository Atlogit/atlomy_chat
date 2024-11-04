'use client'

import { useState, useEffect } from 'react'
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
  const [versions, setVersions] = useState<string[]>([])
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  
  const { data, error, isLoading, execute } = useApi<LexicalValue>()
  const { execute: executeDelete, isLoading: isDeleting } = useApi()
  const versionsApi = useApi<{ versions: string[] }>()

  /**
   * Format version timestamp for display
   */
  const formatVersion = (version: string): string => {
    try {
      // Version format: YYYYMMDD_HHMMSS
      const year = version.slice(0, 4)
      const month = version.slice(4, 6)
      const day = version.slice(6, 8)
      const hour = version.slice(9, 11)
      const minute = version.slice(11, 13)
      const second = version.slice(13, 15)
      
      return `${year}-${month}-${day} ${hour}:${minute}:${second}`
    } catch {
      return version
    }
  }

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
      setVersions([])
    }
  }

  /**
   * Fetches lexical value with specified version
   */
  const fetchLexicalValue = async (version: string | null = null) => {
    if (!lemma.trim()) return

    try {
      // Add timestamp to prevent caching
      const timestamp = new Date().getTime()
      
      // Construct URL with version as a query parameter and cache buster
      const baseUrl = API.lexical.get(lemma.trim())
      const url = new URL(baseUrl, window.location.origin)
      
      // Add version if specified
      if (version) {
        url.searchParams.set('version', version)
      }
      
      // Add cache buster
      url.searchParams.set('_t', timestamp.toString())

      console.log('Fetching lexical value with URL:', url.toString())
      
      await execute(url.toString(), { 
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      })
    } catch (err) {
      console.error('Error fetching lexical value:', err)
    }
  }

  /**
   * Handles the form submission to retrieve a lexical value.
   * 
   * @async
   * @function
   */
  const handleSubmit = async () => {
    if (!lemma.trim()) return

    // Reset version selection
    setSelectedVersion(null)

    // Load versions first
    await loadVersions(lemma.trim())
    
    // Then fetch the latest version
    await fetchLexicalValue(null)
  }

  /**
   * Handles version change
   */
  const handleVersionChange = async (newVersion: string | null) => {
    console.log('Version changed to:', newVersion)
    setSelectedVersion(newVersion)

    // Fetch the selected version
    await fetchLexicalValue(newVersion)
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
    setVersions([])
    setSelectedVersion(null)
  }

  // Clear versions when lemma changes
  useEffect(() => {
    setVersions([])
    setSelectedVersion(null)
  }, [lemma])

  // Debug output for current state
  useEffect(() => {
    if (data) {
      console.log('Current data:', {
        lemma: data.lemma,
        version: selectedVersion || 'current',
        timestamp: new Date().toISOString()
      })
    }
  }, [data, selectedVersion])

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

        {/* Version Selection */}
        {versions.length > 0 && (
          <div className="form-control">
            <label className="label">
              <span className="label-text">Version</span>
            </label>
            <div className="flex gap-2">
              <select
                className="select select-bordered flex-grow"
                value={selectedVersion || ''}
                onChange={(e) => {
                  const newVersion = e.target.value || null
                  handleVersionChange(newVersion)
                }}
                disabled={isLoading}
              >
                <option value="">Current Version</option>
                {versions.map((version) => (
                  <option key={version} value={version}>
                    {formatVersion(version)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Display current version info */}
      {versions.length > 0 && (
        <div className="text-sm text-gray-500 mt-2">
          Currently showing: {selectedVersion ? formatVersion(selectedVersion) : 'Current Version'}
        </div>
      )}

      <ResultsDisplay
        title="Lexical Value"
        content={error ? null : data}
        error={error ? error.message : null}
      />
    </div>
  )
}
