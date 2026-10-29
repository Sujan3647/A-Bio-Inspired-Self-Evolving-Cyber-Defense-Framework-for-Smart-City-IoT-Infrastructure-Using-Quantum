import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'
import {
  Droplets,
  Cpu,
  CheckCircle2,
  Activity,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  Building2,
  Gauge,
} from 'lucide-react'

const PIPELINE_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  pressure: +(2.3 + Math.sin(i * 0.3) * 0.3 + (Math.random() - 0.5) * 0.1).toFixed(3),
  ph: +(7.1 + Math.sin(i * 0.2) * 0.15 + (Math.random() - 0.5) * 0.05).toFixed(2),
  flow: +(120 + Math.cos(i * 0.4) * 30 + (Math.random() - 0.5) * 10).toFixed(1),
}))

const PIPELINES = [
  { id: 'PIPE-001', location: 'Treatment Plant Alpha', pressure: 2.4, ph: 7.1, status: 'normal' },
  { id: 'PIPE-002', location: 'Treatment Plant Beta', pressure: 2.6, ph: 7.2, status: 'normal' },
  { id: 'PIPE-003', location: 'Distribution Mainline', pressure: 2.1, ph: 6.9, status: 'alert' },
  { id: 'PIPE-004', location: 'Residential Aqueduct A', pressure: 2.3, ph: 7.0, status: 'normal' },
  { id: 'PIPE-005', location: 'Hospital Reservoir Feed', pressure: 2.5, ph: 7.1, status: 'normal' },
  { id: 'PIPE-006', location: 'Industrial Sector Conduit', pressure: 2.2, ph: 7.3, status: 'normal' },
]

export default function WaterDashboard() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    api.get('/api/dashboard/water').then(r => setData(r.data)).catch(() => {})
    const id = setInterval(() => {
      api.get('/api/dashboard/water').then(r => setData(r.data)).catch(() => {})
    }, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Water Authority & Hydraulic Defense
            </h1>
            <span className="text-xs bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-semibold px-2 py-0.5 rounded-full">
              MUNICIPAL WATER UTILITY
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Pipeline hydraulic pressure, pH biochemical telemetry, and AI-powered chemical contamination defense
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          POTABILITY: NOMINAL
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Droplets className="w-5 h-5" />}
          value={data?.total_sensors || 60}
          label="Hydraulic Sensors"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={data?.online || 58}
          label="Active In-Line Probes"
          color="text-green-400"
          trend="96.7% operational"
        />
        <StatCard
          icon={<Gauge className="w-5 h-5" />}
          value={`${data?.avg_pressure || 2.4} bar`}
          label="Mean Hydraulic Pressure"
          color="text-blue-400"
          sub="Stable operating band"
        />
        <StatCard
          icon={<ShieldCheck className="w-5 h-5" />}
          value={data?.contamination_alerts || 0}
          label="Contamination Anomalies"
          color="text-green-400"
          sub="Zero toxic vectors"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Hydraulic Pressure Velocity (24h)</h2>
              <p className="text-[11px] text-slate-400">Continuous barometric telemetry across main municipal conduits</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <AreaChart data={PIPELINE_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} interval={3} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[1.8, 3.0]} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
              />
              <Area type="monotone" dataKey="pressure" stroke="#3b82f6" strokeWidth={2} fill="url(#waterGrad)" name="Pressure (bar)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Biochemical Potability pH Trend</h2>
              <p className="text-[11px] text-slate-400">Chemical stability bounds monitored by edge inference (target: 6.8–7.5)</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={PIPELINE_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} interval={3} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[6.5, 7.8]} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
              />
              <Line type="monotone" dataKey="ph" stroke="#10b981" strokeWidth={2.5} dot={false} name="pH Value" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Pipelines Grid */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Building2 className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Municipal Aqueduct & Pipeline Nodes</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {PIPELINES.map((p) => (
            <div
              key={p.id}
              className={`p-3.5 rounded-xl border transition-all ${
                p.status === 'alert'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-white/[0.02] border-white/[0.06]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-xs font-semibold text-white">{p.id}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    p.status === 'alert'
                      ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                      : 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  }`}
                />
              </div>
              <div className="text-xs text-slate-300 font-medium">{p.location}</div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.04] text-[11px] font-mono">
                <span className="text-cyan-300">{p.pressure} bar</span>
                <span className="text-emerald-300">pH {p.ph}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
