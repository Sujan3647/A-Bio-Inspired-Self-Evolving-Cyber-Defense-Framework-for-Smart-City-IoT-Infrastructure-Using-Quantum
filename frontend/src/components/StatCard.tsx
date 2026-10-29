import React from 'react'

interface StatCardProps {
  icon: React.ReactNode
  value: string | number
  label: string
  color?: string
  sub?: string
  pulse?: boolean
  trend?: string
}

const COLOR_MAP: Record<string, { bg: string; text: string; glow: string; border: string }> = {
  'text-cyan-400':    { bg: 'rgba(6,182,212,0.12)',   text: '#22d3ee', glow: 'rgba(6,182,212,0.25)', border: 'rgba(6,182,212,0.25)' },
  'text-indigo-400':  { bg: 'rgba(99,102,241,0.12)',  text: '#818cf8', glow: 'rgba(99,102,241,0.25)', border: 'rgba(99,102,241,0.25)' },
  'text-purple-400':  { bg: 'rgba(168,85,247,0.12)',  text: '#c084fc', glow: 'rgba(168,85,247,0.25)', border: 'rgba(168,85,247,0.25)' },
  'text-emerald-400': { bg: 'rgba(16,185,129,0.12)',  text: '#34d399', glow: 'rgba(16,185,129,0.25)', border: 'rgba(16,185,129,0.25)' },
  'text-green-400':   { bg: 'rgba(34,197,94,0.12)',   text: '#4ade80', glow: 'rgba(34,197,94,0.25)', border: 'rgba(34,197,94,0.25)' },
  'text-red-400':     { bg: 'rgba(244,63,94,0.12)',   text: '#fb7185', glow: 'rgba(244,63,94,0.25)', border: 'rgba(244,63,94,0.25)' },
  'text-red-500':     { bg: 'rgba(239,68,68,0.14)',   text: '#f87171', glow: 'rgba(239,68,68,0.3)', border: 'rgba(239,68,68,0.3)' },
  'text-orange-400':  { bg: 'rgba(249,115,22,0.12)',  text: '#fb923c', glow: 'rgba(249,115,22,0.25)', border: 'rgba(249,115,22,0.25)' },
  'text-yellow-400':  { bg: 'rgba(234,179,8,0.12)',   text: '#facc15', glow: 'rgba(234,179,8,0.25)', border: 'rgba(234,179,8,0.25)' },
  'text-white':       { bg: 'rgba(255,255,255,0.06)', text: '#ffffff', glow: 'rgba(255,255,255,0.15)', border: 'rgba(255,255,255,0.12)' },
}

export default function StatCard({
  icon,
  value,
  label,
  color = 'text-cyan-400',
  sub,
  pulse = false,
  trend,
}: StatCardProps) {
  const c = COLOR_MAP[color] || COLOR_MAP['text-cyan-400']

  return (
    <div
      className="relative overflow-hidden rounded-2xl p-4.5 border border-white/[0.08] transition-all duration-200 hover:border-white/20 hover:-translate-y-0.5 group"
      style={{
        background: 'rgba(13, 21, 39, 0.75)',
        backdropFilter: 'blur(16px)',
      }}
    >
      {/* Ambient glowing radial effect in corner */}
      <div
        className="absolute -top-10 -right-10 w-28 h-28 rounded-full opacity-20 blur-2xl pointer-events-none group-hover:opacity-35 transition-opacity"
        style={{ background: c.glow }}
      />

      <div className="relative flex items-center justify-between mb-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-semibold shrink-0"
          style={{
            background: c.bg,
            color: c.text,
            border: `1px solid ${c.border}`,
          }}
        >
          {icon}
        </div>
        {pulse && (
          <span className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full animate-ping opacity-75"
              style={{ background: c.text }}
            />
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: c.text, boxShadow: `0 0 8px ${c.text}` }}
            />
          </span>
        )}
      </div>

      <div className="relative">
        <div className="text-2xl font-bold tracking-tight text-white flex items-baseline gap-2">
          <span style={{ color: c.text }}>{value}</span>
          {trend && (
            <span className="text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
              {trend}
            </span>
          )}
        </div>
        <div className="text-[11px] text-slate-400 mt-1 font-semibold uppercase tracking-wider">
          {label}
        </div>
        {sub && <div className="text-xs text-slate-500 mt-1 truncate">{sub}</div>}
      </div>
    </div>
  )
}
