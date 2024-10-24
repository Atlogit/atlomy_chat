import { renderHook, act } from '@testing-library/react'
import { useApi } from '../useApi'
import { fetchApi } from '../../utils/api'

jest.mock('../../utils/api')

describe('useApi', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should handle successful API calls', async () => {
    const mockData = { message: 'Success' }
    ;(fetchApi as jest.Mock).mockResolvedValue(mockData)

    const { result } = renderHook(() => useApi<typeof mockData>())

    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()

    await act(async () => {
      await result.current.execute('/api/test')
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toEqual(mockData)
  })

  it('should handle API errors and retry', async () => {
    const mockError = new Error('API Error')
    ;(fetchApi as jest.Mock).mockRejectedValue(mockError)

    const { result } = renderHook(() => useApi())

    await act(async () => {
      await result.current.execute('/api/test')
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toEqual(mockError)
    expect(result.current.data).toBeNull()
    expect(fetchApi).toHaveBeenCalledTimes(3) // 1 initial + 2 retries
  })
})
