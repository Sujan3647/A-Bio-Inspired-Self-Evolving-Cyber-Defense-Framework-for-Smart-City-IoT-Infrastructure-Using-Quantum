import { useState } from 'react'
import { useApi } from '../api/hooks'
import { Link } from 'react-router-dom'
import {
  Bell,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react'

interface AlertItem {
  alert_id: string
  message: string
  severity: string
  acknowledged: boolean
  timestamp: string
  sector: string
}

function getSeverityBadge(severity: string) {
  switch (severity) {
    case 'critical':
      return {
        icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
        border: 'border-l-rose-500 bg-rose-950/20',
      }
    case 'high':
      return {
        icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
        border: 'border-l-amber-500 bg-amber-950/20',
      }
    case 'medium':
      return {
        icon: <Info className="w-4 h-4 text-cyan-400" />,
        border: 'border-l-cyan-500 bg-cyan-950/15',
      }
    default:
      return {
        icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
        border: 'border-l-emerald-500 bg-emerald-950/15',
      }
  }
}

function timeSince(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1)  return 'just now'
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}

export default function NotificationCenter() {
  const [open, setOpen]     = useState(false)
  const { data }            = useApi<any>('/api/alerts/', { refreshInterval: 10000 })
  const alerts: AlertItem[] = data?.alerts || []
  const unread              = alerts.filter(a => !a.acknowledged).length

  return (
    <div className="relative">
      {/* Bell button */}
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-slate-400 hover:text-white transition-all cursor-pointer"
        aria-label="Security Notifications"
      >
        <Bell className="w-4 h-4" />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-rose-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold shadow-md shadow-rose-500/50">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />

          <div
            className="absolute right-0 top-12 w-84 rounded-2xl border border-white/[0.1] shadow-2xl z-50 overflow-hidden"
            style={{
              background: 'rgba(11, 17, 33, 0.95)',
              backdropFilter: 'blur(20px)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(99, 102, 241, 0.15)',
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-indigo-400" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
                  Security Alerts
                </h3>
              </div>
              <span className="text-[11px] font-medium text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-full">
                {unread} unread
              </span>
            </div>

            {/* Alert list */}
            <div className="overflow-y-auto max-h-80 divide-y divide-white/[0.04]">
              {alerts.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  All systems nominal. No active alerts.
                </div>
              ) : (
                alerts.slice(0, 8).map((alert) => {
                  const style = getSeverityBadge(alert.severity)
                  return (
                    <div
                      key={alert.alert_id}
                      className={`px-4 py-3 border-l-4 transition-colors hover:bg-white/[0.03] ${style.border} ${
                        !alert.acknowledged ? 'opacity-100' : 'opacity-60'
                      }`}
                    >
                      <div className="flex items-start gap-2.5">
                        <span className="mt-0.5 shrink-0">{style.icon}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-slate-200 leading-snug">{alert.message}</p>
                          <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-400">
                            <span className="font-semibold uppercase tracking-wider text-indigo-400">{alert.sector}</span>
                            <span>·</span>
                            <span>{timeSince(alert.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-white/[0.08] bg-white/[0.02]">
              <Link
                to="/threats"
                onClick={() => setOpen(false)}
                className="flex items-center justify-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <span>Open Threat Intelligence Feed</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
