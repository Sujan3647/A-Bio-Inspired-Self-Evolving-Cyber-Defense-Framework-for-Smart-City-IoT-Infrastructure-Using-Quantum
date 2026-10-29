import React from 'react'
import type { LiveEvent } from '../hooks/useLiveFeed'
import { useLiveFeed } from '../hooks/useLiveFeed'
import {
  ShieldAlert,
  Layers,
  RefreshCw,
  AlertTriangle,
  Target,
  Brain,
  Cpu,
  Radio,
  Trash2,
} from 'lucide-react'

const EVENT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  attack_detected:         ShieldAlert,
  block_mined:             Layers,
  morphogenesis_triggered: RefreshCw,
  impostor_detected:       AlertTriangle,
  honeypot_triggered:      Target,
  ai_round_completed:      Brain,
  device_status_changed:   Cpu,
}

const EVENT_COLORS: Record<string, string> = {
  attack_detected:         'text-rose-400 bg-rose-500/10 border-rose-500/20',
  block_mined:             'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  morphogenesis_triggered: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  impostor_detected:       'text-amber-400 bg-amber-500/10 border-amber-500/20',
  honeypot_triggered:      'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  ai_round_completed:      'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  device_status_changed:   'text-slate-400 bg-slate-500/10 border-slate-500/20',
}

function EventRow({ event }: { event: LiveEvent }) {
  const IconComponent = EVENT_ICONS[event.type] || Radio
  const styleColor = EVENT_COLORS[event.type] || 'text-slate-400 bg-slate-500/10 border-slate-500/20'
  const label = event.type.replace(/_/g, ' ')
  const data = event.data || {}

  const summary = (() => {
    if (event.type === 'attack_detected')
      return `${(data.attack_type as string)?.replace(/_/g, ' ')} detected on ${data.sector} sector (${data.severity})`
    if (event.type === 'block_mined')
      return `Immune block #${data.block_index} committed to chain (${data.attack_records} attack signatures)`
    if (event.type === 'morphogenesis_triggered')
      return `Adaptive action: ${(data.action as string)?.replace(/_/g, ' ')} active in ${data.sector}`
    if (event.type === 'impostor_detected')
      return `QBF identity failure: ${data.verdict} in ${data.sector} (fidelity: ${data.fidelity_score})`
    if (event.type === 'honeypot_triggered')
      return `Adversary trap engaged: ${(data.attack_type as string)?.replace(/_/g, ' ')} captured in ${data.sector}`
    if (event.type === 'ai_round_completed')
      return `Federated learning round ${data.round} converged (accuracy: ${data.accuracy}%)`
    return `Node status transition: ${data.device_id} → ${data.new_status}`
  })()

  return (
    <div className="flex items-center gap-3 py-2 px-2.5 rounded-lg hover:bg-white/[0.03] transition-colors border-b border-white/[0.04] last:border-0 text-xs">
      <div className={`p-1.5 rounded-lg border shrink-0 ${styleColor}`}>
        <IconComponent className="w-3.5 h-3.5" />
      </div>
      <div className="w-32 shrink-0 font-medium text-slate-300 capitalize truncate">
        {label}
      </div>
      <div className="flex-1 min-w-0 text-slate-400 truncate">
        {summary}
      </div>
    </div>
  )
}

interface LiveFeedPanelProps {
  maxEvents?: number
  className?: string
}

export default function LiveFeedPanel({ maxEvents = 20, className = '' }: LiveFeedPanelProps) {
  const { events, connected, clearEvents } = useLiveFeed({ maxEvents })

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Live Defense Event Stream</h2>
            <p className="text-[11px] text-slate-400">WebSocket-driven real-time node & threat telemetry</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08]">
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
            <span className={`text-[11px] font-semibold ${connected ? 'text-emerald-400' : 'text-rose-400'}`}>
              {connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          <button
            onClick={clearEvents}
            className="text-slate-500 hover:text-slate-300 p-1 rounded hover:bg-white/[0.05] transition-colors cursor-pointer"
            title="Clear Stream"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="overflow-y-auto max-h-72 space-y-0.5 divide-y divide-transparent">
        {events.length === 0 ? (
          <div className="text-slate-500 text-xs text-center py-10 flex flex-col items-center justify-center gap-2">
            <Radio className="w-6 h-6 text-slate-600 animate-pulse" />
            <span>Listening for real-time security events across smart city grid...</span>
          </div>
        ) : (
          events.map((event) => (
            <EventRow key={event.event_id} event={event} />
          ))
        )}
      </div>
    </div>
  )
}
