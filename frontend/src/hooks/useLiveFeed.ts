/**
 * ImmunoGrid — Live Feed WebSocket Hook
 * Connects to the backend WebSocket and streams live security events.
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export interface LiveEvent {
  event_id: number
  type: string
  data: Record<string, unknown>
  timestamp?: string
}

interface UseLiveFeedOptions {
  maxEvents?: number
  onEvent?: (event: LiveEvent) => void
}

export function useLiveFeed({ maxEvents = 50, onEvent }: UseLiveFeedOptions = {}) {
  const [events, setEvents] = useState<LiveEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    const wsUrl = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/api/ws/live'
    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => { setConnected(true); setError(null) }

      ws.onmessage = (msg) => {
        try {
          const event: LiveEvent = JSON.parse(msg.data)
          if (event.type === 'connected') return
          setEvents((prev) => [event, ...prev].slice(0, maxEvents))
          onEvent?.(event)
        } catch { /* ignore */ }
      }

      ws.onerror = () => { setError('WebSocket error'); setConnected(false) }

      ws.onclose = () => {
        setConnected(false)
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    } catch {
      setError('Failed to connect to live feed')
    }
  }, [maxEvents, onEvent])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  const clearEvents = useCallback(() => setEvents([]), [])

  return { events, connected, error, clearEvents }
}
