/**
 * ImmunoGrid — Reusable API Hooks
 * Custom React hooks for data fetching with auto-refresh.
 */

import { useEffect, useState, useCallback } from 'react'
import api from './client'

interface UseApiOptions {
  refreshInterval?: number   // ms — set 0 to disable auto-refresh
  enabled?: boolean
}

interface UseApiResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useApi<T>(
  url: string,
  { refreshInterval = 0, enabled = true }: UseApiOptions = {},
): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    if (!enabled) return
    try {
      const res = await api.get<T>(url)
      setData(res.data)
      setError(null)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Request failed')
    } finally {
      setLoading(false)
    }
  }, [url, enabled])

  useEffect(() => {
    fetch()
    if (refreshInterval > 0) {
      const interval = setInterval(fetch, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [fetch, refreshInterval])

  return { data, loading, error, refetch: fetch }
}

// ── Convenience hooks ─────────────────────────────────────────────────────────

export const useCommandCenter = (refresh = 5000) =>
  useApi<any>('/api/dashboard/command-center', { refreshInterval: refresh })

export const useDeviceStats = (refresh = 10000) =>
  useApi<any>('/api/devices/stats', { refreshInterval: refresh })

export const useThreatSummary = (refresh = 5000) =>
  useApi<any>('/api/threats/summary', { refreshInterval: refresh })

export const useBlockchainStats = (refresh = 8000) =>
  useApi<any>('/api/blockchain/stats', { refreshInterval: refresh })

export const useQuantumStats = (refresh = 10000) =>
  useApi<any>('/api/quantum/stats', { refreshInterval: refresh })

export const useAIStats = (refresh = 10000) =>
  useApi<any>('/api/ai/stats', { refreshInterval: refresh })

export const useHoneypotStats = (refresh = 8000) =>
  useApi<any>('/api/honeypot/stats', { refreshInterval: refresh })

export const useSimulationStatus = (refresh = 3000) =>
  useApi<any>('/api/simulation/status', { refreshInterval: refresh })

export const useAlerts = (refresh = 5000) =>
  useApi<any>('/api/alerts/', { refreshInterval: refresh })
