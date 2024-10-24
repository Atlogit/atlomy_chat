'use client'

import { useState, useCallback } from 'react'

interface UseLoadingReturn<T> {
  isLoading: boolean
  error: string | null
  execute: (promise: Promise<T>) => Promise<T | undefined>
  clearError: () => void
}

export function useLoading<T = unknown>(): UseLoadingReturn<T> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (promise: Promise<T>): Promise<T | undefined> => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await promise
      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unknown error occurred'
      setError(message)
      return undefined
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    isLoading,
    error,
    execute,
    clearError,
  }
}

export function useLoadingWithProgress<T = unknown>() {
  const [progress, setProgress] = useState<{ current: number; total: number }>({
    current: 0,
    total: 0,
  })
  const loading = useLoading<T>()

  const updateProgress = useCallback((current: number, total: number) => {
    setProgress({ current, total })
  }, [])

  const resetProgress = useCallback(() => {
    setProgress({ current: 0, total: 0 })
  }, [])

  return {
    ...loading,
    progress,
    updateProgress,
    resetProgress,
  }
}
