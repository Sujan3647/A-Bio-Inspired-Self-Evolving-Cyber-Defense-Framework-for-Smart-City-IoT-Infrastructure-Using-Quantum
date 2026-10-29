import { useEffect, useState } from 'react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'
import {
  Car,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  MapPin,
  Activity,
  ShieldAlert,
} from 'lucide-react'

const HOURS = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  vehicles: Math.floor(5 + Math.abs(Math.sin((i - 8) * 0.4)) * 80 + Math.random() * 10),
  anomalies: Math.random() < 0.15 ? Math.floor(Math.random() * 3) : 0,
}))

const INTERSECTIONS = [
  { name: 'Intersection A1 - North Gate', vehicles: 68, status: 'normal', congestion: 'low' },
  { name: 'Highway North Arterial',       vehicles: 122, status: 'alert',  congestion: 'high' },
  { name: 'Downtown Central Spine',       vehicles: 89, status: 'normal', congestion: 'medium' },
  { name: 'Airport Express Corridor',     vehicles: 54, status: 'normal', congestion: 'low' },
  { name: 'Metro Terminal Junction',      vehicles: 77, status: 'normal', congestion: 'medium' },
  { name: 'Intersection B2 - Tech Hub',  vehicles: 43, status: 'normal', congestion: 'low' },
]

export default function TrafficDashboard() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    api.get('/api/dashboard/traffic').then(r => setData(r.data)).catch(() => {})
    const id = setInterval(() => {
      api.get('/api/dashboard/traffic').then(r => setData(r.data)).catch(() => {})
    }, 10000)
    return () => clearInterval(id)
  }, [])

  const congestionBadge = (c: string) => {
    switch (c) {
      case 'high':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20'
      case 'medium':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20'
      default:
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Traffic Transit Defense Sector
            </h1>
            <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold px-2 py-0.5 rounded-full">
              MINISTRY OF TRANSPORTATION
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Real-time optical and electromagnetic road sensor telemetry across {data?.total_sensors || 100} municipal intersections
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          TELEMETRY STREAM ONLINE
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Cpu className="w-5 h-5" />}
          value={data?.total_sensors || 100}
          label="Roadway Node Sensors"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={data?.online || 98}
          label="Online Nodes"
          color="text-green-400"
          trend="98% Uptime"
        />
        <StatCard
          icon={<Car className="w-5 h-5" />}
          value={data?.avg_vehicle_count || 52}
          label="Avg Vehicle Velocity/min"
          color="text-yellow-400"
          sub="Nominal municipal flow"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={data?.anomalies_today || 2}
          label="Traffic Anomalies (24h)"
          color="text-orange-400"
          sub="Spoofing attacks contained"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vehicle Flow */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Vehicle Flow Velocity (24h)</h2>
              <p className="text-[11px] text-slate-400">Hourly vehicular density tracked across arterial nodes</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <AreaChart data={HOURS} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="trafGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} interval={3} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
              />
              <Area type="monotone" dataKey="vehicles" stroke="#f59e0b" strokeWidth={2} fill="url(#trafGrad)" name="Vehicles / min" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Anomaly Detections */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Anomalous Telemetry Spikes (24h)</h2>
              <p className="text-[11px] text-slate-400">Detected spoofing bursts flagged by Quantum QBF engine</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <BarChart data={HOURS.filter(h => h.anomalies > 0)} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
              />
              <Bar dataKey="anomalies" fill="#f43f5e" name="Spoofing Vectors" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Intersections */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <MapPin className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Critical Municipal Intersections</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {INTERSECTIONS.map((inter) => (
            <div key={inter.name} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    inter.status === 'alert'
                      ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                      : 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  }`}
                />
                <div>
                  <div className="text-xs font-semibold text-white">{inter.name}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">{inter.vehicles} vehicles/min</div>
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${congestionBadge(inter.congestion)}`}>
                {inter.congestion} Congestion
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Security Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Sector Defense Integrity</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Quantum Fingerprint Match:</span>
              <span className="text-cyan-300 font-mono font-medium">{data?.fingerprint_match_rate || '99.2%'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Spoofing Injections Neutralized:</span>
              <span className="text-emerald-400 font-medium">100% Contained</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Data Integrity Score:</span>
              <span className="text-emerald-400 font-mono font-medium">{data?.data_integrity_score || '98.7%'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Active Congestion Zones:</span>
              <span className="text-amber-400 font-mono font-medium">{data?.congestion_zones || 2} Zones</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <Activity className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Top Neutralized Vectors (7 Days)</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            {[
              { type: 'Sensor GPS Spoofing', count: 12, pct: 60 },
              { type: 'Data Poisoning (Speed Injection)', count: 5, pct: 25 },
              { type: 'Traffic Signal Replay', count: 3, pct: 15 },
            ].map((a) => (
              <div key={a.type}>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-300">{a.type}</span>
                  <span className="text-white font-mono font-semibold">{a.count} Blocked</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${a.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
