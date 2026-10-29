import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'
import {
  Zap,
  Cpu,
  CheckCircle2,
  Activity,
  AlertTriangle,
  TrendingUp,
  Building2,
  Gauge,
  ShieldAlert,
} from 'lucide-react'

const LOAD_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  load: Math.round(30 + Math.abs(Math.sin((i - 8) * 0.35)) * 60 + Math.random() * 5),
  voltage: +(229 + Math.sin(i * 0.4) * 3 + (Math.random() - 0.5)).toFixed(1),
  frequency: +(49.98 + (Math.random() - 0.5) * 0.08).toFixed(3),
}))

const SUBSTATIONS = [
  { id: 'SS-NORTH', location: 'Substation North 110kV', voltage: 230.4, load: 78, status: 'normal', zone: 'ZONE-1' },
  { id: 'SS-SOUTH', location: 'Substation South Terminal', voltage: 228.9, load: 65, status: 'normal', zone: 'ZONE-2' },
  { id: 'SS-EAST',  location: 'Grid East Hydro Feeder', voltage: 231.2, load: 82, status: 'alert',  zone: 'ZONE-3' },
  { id: 'IND-FEED', location: 'Heavy Industrial Busbar', voltage: 229.5, load: 91, status: 'normal', zone: 'ZONE-4' },
  { id: 'HOSP-GRD', location: 'Hospital Redundant Grid', voltage: 230.1, load: 55, status: 'normal', zone: 'ZONE-5' },
  { id: 'GOVT-BLD', location: 'Civic Administration Feed', voltage: 229.8, load: 43, status: 'normal', zone: 'ZONE-6' },
]

export default function PowerDashboard() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    api.get('/api/dashboard/power').then(r => setData(r.data)).catch(() => {})
    const id = setInterval(() => {
      api.get('/api/dashboard/power').then(r => setData(r.data)).catch(() => {})
    }, 8000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Electrical Grid & Energy Sector Defense
            </h1>
            <span className="text-xs bg-amber-500/10 border border-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded-full">
              MINISTRY OF ENERGY
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Real-time high-voltage substation telemetry · Grid load balancing · Frequency stabilization and cyber fault containment
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          SYNCHRONOUS FREQUENCY STABLE
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          value={data?.total_sensors || 80}
          label="Grid Node Sensors"
          color="text-yellow-400"
          pulse
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={data?.online || 78}
          label="Active Transformers"
          color="text-green-400"
          trend="97.5% Uptime"
        />
        <StatCard
          icon={<Gauge className="w-5 h-5" />}
          value={`${data?.avg_load || 69}%`}
          label="Mean Grid Capacity Load"
          color="text-orange-400"
          sub="Optimal reserve margin"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={data?.faults_today || 2}
          label="Neutralized Grid Faults"
          color="text-red-400"
          sub="Replay attacks prevented"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Power Grid Demand Curve (24h)</h2>
              <p className="text-[11px] text-slate-400">Total electrical capacity load percentage across city feeders</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={LOAD_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} interval={3} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
                formatter={(v: any) => [`${v}%`]}
              />
              <Line type="monotone" dataKey="load" stroke="#f59e0b" strokeWidth={2.5} dot={false} name="Grid Load %" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Distribution Voltage Stability (24h)</h2>
              <p className="text-[11px] text-slate-400">Measured line voltage stability bounds (nominal 230V ± 2%)</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={LOAD_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} interval={3} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[224, 236]} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
                formatter={(v: any) => [`${v} V`]}
              />
              <Line type="monotone" dataKey="voltage" stroke="#818cf8" strokeWidth={2.5} dot={false} name="Voltage (V)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Substations Grid */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Building2 className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-white">High-Voltage Substation Nodes</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {SUBSTATIONS.map((s) => (
            <div
              key={s.id}
              className={`p-3.5 rounded-xl border transition-all ${
                s.status === 'alert'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-white/[0.02] border-white/[0.06]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-xs font-semibold text-white">{s.id}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    s.status === 'alert'
                      ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                      : 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  }`}
                />
              </div>
              <div className="text-xs text-slate-300 font-medium">{s.location}</div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.04] text-[11px] font-mono">
                <span className="text-amber-300">{s.voltage} V</span>
                <span className="text-cyan-300 font-bold">{s.load}% Capacity</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
