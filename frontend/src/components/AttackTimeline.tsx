import React from 'react'
import {
  ShieldAlert,
  Layers,
  Atom,
  Brain,
  Target,
  Lock,
  RefreshCw,
  Zap,
  Activity,
  AlertTriangle,
  Radio,
} from 'lucide-react'

interface TimelineEvent {
  threat_id: string
  attack_type: string
  severity: string
  target_sector: string
  detected_by: string
  status: string
  timestamp: string
  morphogenesis_triggered?: boolean
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'border-rose-500/40 bg-rose-950/20 text-rose-300',
  high:     'border-amber-500/40 bg-amber-950/20 text-amber-300',
  medium:   'border-cyan-500/40 bg-cyan-950/15 text-cyan-300',
  low:      'border-emerald-500/40 bg-emerald-950/15 text-emerald-300',
}

const ATTACK_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  spoofing:          Radio,
  ddos:              Activity,
  data_poisoning:    AlertTriangle,
  replay_attack:     RefreshCw,
  man_in_the_middle: ShieldAlert,
  ransomware:        Lock,
  unknown:           AlertTriangle,
}

const DETECTOR_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  quantum_fingerprint: Atom,
  ai_brain:            Brain,
  honeypot:            Target,
  blockchain_memory:   Layers,
  pqc_signature:       Lock,
  combined:            ShieldAlert,
}

interface AttackTimelineProps {
  events: TimelineEvent[]
  maxItems?: number
  showMorphogenesis?: boolean
}

function timeSince(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function AttackTimeline({
  events,
  maxItems = 10,
  showMorphogenesis = true,
}: AttackTimelineProps) {
  const visible = events.slice(0, maxItems)

  if (visible.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 text-xs">
        No attack events recorded on timeline
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-4 top-2 bottom-2 w-px bg-white/[0.08]" />

      <div className="space-y-3">
        {visible.map((event) => {
          const AttackIcon = ATTACK_ICONS[event.attack_type] || AlertTriangle
          const DetectorIcon = DETECTOR_ICONS[event.detected_by] || Atom

          return (
            <div key={event.threat_id} className="relative flex gap-3 pl-9">
              {/* Dot on timeline */}
              <div
                className={`absolute left-2.5 top-3.5 w-3 h-3 rounded-full border-2 z-10 ${
                  event.severity === 'critical' ? 'bg-rose-500 border-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.6)]' :
                  event.severity === 'high'     ? 'bg-amber-500 border-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)]' :
                  event.severity === 'medium'   ? 'bg-cyan-500 border-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.6)]' :
                  'bg-emerald-500 border-emerald-400'
                }`}
              />

              {/* Card */}
              <div
                className={`flex-1 rounded-xl border p-3 text-xs transition-all duration-150 hover:border-white/20 ${
                  SEVERITY_COLORS[event.severity] || SEVERITY_COLORS.low
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AttackIcon className="w-3.5 h-3.5" />
                    <span className="font-semibold text-white capitalize">
                      {event.attack_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-slate-400 text-[11px] capitalize">
                      → {event.target_sector} Sector
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="text-slate-400">{timeSince(event.timestamp)}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                        event.status === 'mitigated' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        event.status === 'investigating' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                        'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                      }`}
                    >
                      {event.status}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-2 pt-2 border-t border-white/[0.06] text-[11px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <DetectorIcon className="w-3 h-3 text-indigo-400" />
                    <span className="capitalize">{event.detected_by?.replace(/_/g, ' ')}</span>
                  </span>
                  {showMorphogenesis && event.morphogenesis_triggered && (
                    <span className="flex items-center gap-1 text-purple-400 font-medium">
                      <Zap className="w-3 h-3" />
                      Morphogenesis Triggered
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
