'use client'

import { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue } from '../../../utils/api'
import { Version } from '../../../utils/api/types/lexical'

// Utility function for generating stable, unique keys
const generateStableKey = (...parts: (string | number | undefined | null)[]) => {
  const validParts = parts
    .filter(part => part !== undefined && part !== null)
    .map(part => String(part).trim())
    .filter(part => part !== '')

  return validParts.length > 0 
    ? validParts.join('-').replace(/[^a-zA-Z0-9-]/g, '_')
    : 'default-key'
}

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
  const [versions, setVersions] = useState<Version[]>([])
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  const [currentLexicalValue, setCurrentLexicalValue] = useState<LexicalValue | null>(null)
  
  const { data, error, isLoading, execute } = useApi<LexicalValue>()
  const { execute: executeDelete, isLoading: isDeleting } = useApi()
  const versionsApi = useApi<{ versions: Version[] }>()

  /**
   * Format version timestamp for display
   */
  const formatVersion = (version: Version): string => {
    try {
      // Version format: YYYYMMDD_HHMMSS
      const versionStr = version.version
      const year = versionStr.slice(0, 4)
      const month = versionStr.slice(4, 6)
      const day = versionStr.slice(6, 8)
      const hour = versionStr.slice(9, 11)
      const minute = versionStr.slice(11, 13)
      const second = versionStr.slice(13, 15)
      
      const formattedDate = `${year}-${month}-${day} ${hour}:${minute}:${second}`
      return version.model 
        ? `${formattedDate} (${version.model})` 
        : formattedDate
    } catch {
      return version.version
    }
  }

  /**
   * Extracts LLM configuration from metadata
   */
  const extractLLMConfig = (metadata: any) => {
    console.log('Full Metadata for LLM Config Extraction:', JSON.stringify(metadata, null, 2))

    // Check multiple potential paths for LLM configuration
    const configPaths = [
      metadata?.llm_config,
      metadata?.metadata?.llm_config,
      metadata?.config?.llm_config,
      metadata?.llm_config?.config,
      metadata
    ]

    // Find the first non-empty configuration
    const config = configPaths.find(cfg => 
      cfg && 
      typeof cfg === 'object' && 
      Object.keys(cfg).length > 0 && 
      (cfg.model_id || cfg.temperature !== undefined || cfg.top_p !== undefined)
    )

    // If no config found, return an empty object
    const extractedConfig = config || {}

    console.log('Extracted LLM Config:', JSON.stringify(extractedConfig, null, 2))
    return extractedConfig
  }  
  /**
   * Loads available versions for a lemma
   */
  const loadVersions = async (lemma: string) => {
    try {
      const result = await versionsApi.execute(API.lexical.versions(lemma), { method: 'GET' })
      if (result?.versions) {
        setVersions(result.versions)
        // Set default version if available
        if (result.versions.length > 0) {
          setSelectedVersion(result.versions[0].version)
        }
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
      
      const result = await execute(url.toString(), { 
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      })

      if (result) {
        setCurrentLexicalValue(result)
        
        // Log full metadata for debugging
        console.log('Full Metadata:', JSON.stringify(result.metadata, null, 2))
        
        // Extract and log LLM config
        const llmConfig = extractLLMConfig(result.metadata)
        console.log('Extracted LLM Config:', JSON.stringify(llmConfig, null, 2))
      }
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
    setCurrentLexicalValue(null)
  }

  // Clear versions when lemma changes
  useEffect(() => {
    setVersions([])
    setSelectedVersion(null)
    setCurrentLexicalValue(null)
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
                {versions.map((version, index) => (
                  <option 
                    key={generateStableKey('version', version.version, version.created_at, index)} 
                    value={version.version}
                  >
                    {formatVersion(version)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Currently Showing Section */}
      {(selectedVersion || currentLexicalValue) && (
        <div className="text-sm text-gray-500 mt-2">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="font-semibold">Currently showing:</span>{' '}
              {selectedVersion ? formatVersion(versions.find(v => v.version === selectedVersion)!) : 'Current Version'}
            </div>
            {currentLexicalValue?.metadata && (
              <div>
                <span className="font-semibold">LLM Configuration:</span>
                <div className="grid grid-cols-2 gap-1 text-xs">
                  {Object.entries(extractLLMConfig(currentLexicalValue.metadata)).map(([key, value]) => (
                    <div key={key}>
                      <span className="font-medium">{key}:</span>{' '}
                      {value === null || value === undefined 
                        ? 'N/A' 
                        : typeof value === 'object' 
                          ? JSON.stringify(value) 
                          : String(value)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
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
