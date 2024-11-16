'use client'

import { useState, useEffect } from 'react'
import { Button } from '../../../components/ui/Button'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'
import { useApi } from '../../../hooks/useApi'
import { API, LexicalValue } from '../../../utils/api'

/**
 * UpdateForm Component
 * 
 * This component provides a form for updating existing lexical values.
 * It allows users to search for a lemma, view its current translation,
 * and update the translation if needed.
 *
 * @component
 */
export function UpdateForm() {
  const [lemma, setLemma] = useState('')
  const [translation, setTranslation] = useState('')
  const { data: searchData, error: searchError, isLoading: isSearching, execute: executeSearch } = useApi<LexicalValue>()
  const { data: updateData, error: updateError, isLoading: isUpdating, execute: executeUpdate } = useApi<LexicalValue>()

  /**
   * Handles the search operation to fetch the current lexical value.
   * 
   * @async
   * @function
   */
  const handleSearch = async () => {
    if (!lemma.trim()) return

    await executeSearch(API.lexical.get(lemma.trim()))
  }

  // Update translation when search data changes
  useEffect(() => {
    if (searchData && searchData.translation) {
      setTranslation(searchData.translation)
    }
  }, [searchData])

  /**
   * Handles the update operation to modify the lexical value.
   * 
   * @async
   * @function
   */
  const handleUpdate = async () => {
    if (!lemma.trim() || !translation.trim()) return

    await executeUpdate(API.lexical.update, {
      method: 'PUT',
      body: JSON.stringify({
        lemma: lemma.trim(),
        translation: translation.trim()
      }),
    })

    // Clear form after successful submission
    if (updateData) {
      setLemma('')
      setTranslation('')
    }
  }

  return (
    <div className="form-control gap-4">
      <div className="flex gap-4">
        <div className="flex-1">
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
        <div className="flex items-end">
          <Button
            onClick={handleSearch}
            isLoading={isSearching}
            disabled={!lemma.trim()}
            variant="outline"
          >
            Search
          </Button>
        </div>
      </div>

      <div>
        <label className="label">
          <span className="label-text">Translation</span>
        </label>
        <textarea
          className="textarea textarea-bordered w-full h-24"
          placeholder="Enter updated translation..."
          value={translation}
          onChange={(e) => setTranslation(e.target.value)}
        />
      </div>

      <Button
        onClick={handleUpdate}
        isLoading={isUpdating}
        disabled={!lemma.trim() || !translation.trim()}
      >
        Update Lexical Value
      </Button>

      <ResultsDisplay
        title="Updated Lexical Value"
        content={updateError ? null : updateData ? `${updateData.lemma}: ${updateData.translation}` : null}
        error={searchError ? searchError.message : updateError ? updateError.message : null}
      />
    </div>
  )
}
