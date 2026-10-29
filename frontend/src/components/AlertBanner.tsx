import { useEffect, useState } from 'react'
import api from '../api/client'
import { ShieldAlert, X } from 'lucide-react'

interface Alert {
  alert_id: string
  message: string
  severity: string
  acknowledged: boolean
  timestamp: string
  sector: string
}

export default function AlertBanner() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  useEffect(() => {
    api.get('/api/alerts/')
      .then(r => setAlerts(r.data.alerts || []))
      .catch(() => {})
  }, [])

  const unread = alerts.filter(
    a => !a.acknowledged && !dismissed.has(a.alert_id) && a.severity === 'critical'
  )

  if (unread.length === 0) return null

  return (
    <div className="mx-6 mt-4 space-y-2">
      {unread.slice(0, 2).map((alert) => (
        <div
          key={alert.alert_id}
          className="flex items-center justify-between bg-rose-950/40 border border-rose-500/40 backdrop-blur-md rounded-xl px-4 py-3 shadow-lg shadow-rose-950/40"
        >
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400 shrink-0">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <p className="text-sm font-semibold text-rose-200">{alert.message}</p>
              <p className="text-xs text-rose-400/80 mt-0.5">
                Sector: <span className="font-semibold capitalize text-rose-300">{alert.sector}</span> · Detected {new Date(alert.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <button
            onClick={() => setDismissed(prev => new Set([...prev, alert.alert_id]))}
            className="text-rose-400 hover:text-rose-200 hover:bg-rose-500/20 p-1.5 rounded-lg transition-colors ml-4 shrink-0 cursor-pointer"
            title="Acknowledge Alert"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
