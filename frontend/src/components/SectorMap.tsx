import React, { useEffect, useState } from 'react'
import {
  Car,
  Activity,
  Droplets,
  Zap,
  Camera,
  Train,
  Plane,
  Landmark,
  ShieldAlert,
  MapPin,
  ShieldCheck,
} from 'lucide-react'

export interface Sector {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  devices: number
  threats: number
  status: 'normal' | 'alert' | 'critical' | 'isolated'
  fpMatchRate: number
}

const DEFAULT_SECTORS: Sector[] = [
  { id: 'traffic',     name: 'Traffic Transit',    icon: Car,      devices: 100, threats: 0, status: 'normal',   fpMatchRate: 99.2 },
  { id: 'hospital',    name: 'Healthcare Grid',    icon: Activity, devices: 80,  threats: 1, status: 'alert',    fpMatchRate: 98.7 },
  { id: 'water',       name: 'Water Utilities',    icon: Droplets, devices: 60,  threats: 0, status: 'normal',   fpMatchRate: 99.4 },
  { id: 'power',       name: 'Energy & Power Grid', icon: Zap,      devices: 80,  threats: 0, status: 'normal',   fpMatchRate: 98.9 },
  { id: 'surveillance',name: 'City Surveillance',  icon: Camera,   devices: 80,  threats: 0, status: 'normal',   fpMatchRate: 99.1 },
  { id: 'metro',       name: 'Metro Transit System', icon: Train,   devices: 50,  threats: 0, status: 'normal',   fpMatchRate: 99.4 },
  { id: 'airport',     name: 'International Airport', icon: Plane,   devices: 30,  threats: 1, status: 'alert',    fpMatchRate: 98.9 },
  { id: 'government',  name: 'Civic Government',  icon: Landmark, devices: 20,  threats: 0, status: 'normal',   fpMatchRate: 99.7 },
]

const STATUS_STYLES = {
  normal:   'bg-emerald-950/20 border-emerald-500/20 hover:border-emerald-500/40 text-emerald-400',
  alert:    'bg-amber-950/25 border-amber-500/30 hover:border-amber-500/50 text-amber-400 animate-pulse',
  critical: 'bg-rose-950/30 border-rose-500/40 hover:border-rose-500/60 text-rose-400',
  isolated: 'bg-slate-900/60 border-slate-700/60 text-slate-500 opacity-60',
}

const STATUS_DOT = {
  normal:   'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]',
  alert:    'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)]',
  critical: 'bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.6)]',
  isolated: 'bg-slate-500',
}

interface SectorMapProps {
  onSectorClick?: (sector: Sector) => void
}

export default function SectorMap({ onSectorClick }: SectorMapProps) {
  const [sectors, setSectors] = useState<Sector[]>(DEFAULT_SECTORS)
  const [selected, setSelected] = useState<string | null>(null)

  // Simulate subtle real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSectors(prev => prev.map(s => ({
        ...s,
        threats: Math.random() < 0.04 ? s.threats + 1 : Math.max(0, s.threats - (Math.random() < 0.25 ? 1 : 0)),
        status: s.threats > 2 ? 'critical' : s.threats > 0 ? 'alert' : 'normal',
        fpMatchRate: Math.min(100, s.fpMatchRate + (Math.random() - 0.5) * 0.08),
      })))
    }, 6000)
    return () => clearInterval(interval)
  }, [])

  const handleClick = (sector: Sector) => {
    setSelected(sector.id === selected ? null : sector.id)
    onSectorClick?.(sector)
  }

  const totalThreats = sectors.reduce((sum, s) => sum + s.threats, 0)
  const alertSectors = sectors.filter(s => s.status !== 'normal').length

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Smart City Sector Topology</h2>
            <p className="text-[11px] text-slate-400">Autonomous quantum fingerprint telemetry across 8 critical zones</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/60 border border-white/[0.06] text-slate-400">
            Active Threats: <span className="text-rose-400 font-bold ml-1">{totalThreats}</span>
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/60 border border-white/[0.06] text-slate-400">
            Alert Sectors: <span className="text-amber-400 font-bold ml-1">{alertSectors}</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {sectors.map((sector) => {
          const Icon = sector.icon
          return (
            <button
              key={sector.id}
              onClick={() => handleClick(sector)}
              className={`rounded-xl border p-3.5 text-left transition-all duration-200 cursor-pointer relative group ${
                STATUS_STYLES[sector.status]
              } ${
                selected === sector.id ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-900' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-white/[0.05] border border-white/[0.08]">
                  <Icon className="w-4 h-4" />
                </div>
                <span className={`w-2 h-2 rounded-full ${STATUS_DOT[sector.status]}`} />
              </div>
              <div className="text-xs font-semibold text-white group-hover:text-indigo-200 transition-colors">
                {sector.name}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {sector.devices} Active Nodes
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.06] text-[11px]">
                <span className="text-cyan-400 font-mono">QBF: {sector.fpMatchRate.toFixed(1)}%</span>
                {sector.threats > 0 ? (
                  <span className="text-rose-400 font-bold">{sector.threats} Threat</span>
                ) : (
                  <span className="text-emerald-400 font-medium">Secure</span>
                )}
              </div>
            </button>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5 mt-4 pt-3 border-t border-white/[0.06] text-[11px] text-slate-400">
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" /> Nominal
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.8)]" /> Anomaly Alert
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-rose-400 shadow-[0_0_6px_rgba(244,63,94,0.8)]" /> High Severity
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-slate-500" /> Isolated Node
        </span>
      </div>
    </div>
  )
}
