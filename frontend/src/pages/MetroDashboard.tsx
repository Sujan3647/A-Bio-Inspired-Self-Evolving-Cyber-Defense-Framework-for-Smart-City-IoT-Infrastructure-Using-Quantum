import { useEffect, useState } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import StatCard from '../components/StatCard'
import {
  Train,
  Cpu,
  CheckCircle2,
  Users,
  Clock,
  TrendingUp,
  Building2,
  ShieldCheck,
} from 'lucide-react'

const MOCK_FLOW = Array.from({ length: 20 }, (_, i) => ({
  time: `${5 + i}:00`,
  passengers: Math.floor(100 + Math.sin(i * 0.5) * 200 + Math.random() * 50),
}))

export default function MetroDashboard() {
  const [stats] = useState({
    total_sensors: 50,
    online: 48,
    stations_monitored: 6,
    avg_passengers: 312,
    delays_today: 2,
    security_alerts: 0,
  })

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Metro & Urban Rail Transit Defense
            </h1>
            <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold px-2 py-0.5 rounded-full">
              MASS TRANSIT AUTHORITY
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Automated train signaling protection · Turnstile passenger flow tracking · Trackside vibration sensors
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          RAIL TELEMETRY SYNCHRONIZED
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Cpu className="w-5 h-5" />}
          value={stats.total_sensors}
          label="Trackside IoT Sensors"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={stats.online}
          label="Active Signaling Nodes"
          color="text-green-400"
          trend="96% Uptime"
        />
        <StatCard
          icon={<Users className="w-5 h-5" />}
          value={stats.avg_passengers}
          label="Avg Passenger Throughput/hr"
          color="text-yellow-400"
          sub="Turnstile verification"
        />
        <StatCard
          icon={<Clock className="w-5 h-5" />}
          value={stats.delays_today}
          label="Schedule Deviation Incidents"
          color="text-orange-400"
          sub="No cyber disruptions"
        />
      </div>

      {/* Passenger Flow Area Chart */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Passenger Flow Velocity (Today)</h2>
            <p className="text-[11px] text-slate-400">Aggregated turnstile ingress/egress across municipal rapid transit lines</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={210}>
          <AreaChart data={MOCK_FLOW} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="metroGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: 'rgba(11, 17, 33, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.75rem',
              }}
            />
            <Area type="monotone" dataKey="passengers" stroke="#3b82f6" strokeWidth={2} fill="url(#metroGrad)" name="Passengers / hr" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Station Status Grid */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Building2 className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Station Interlock & Signaling Status</h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {['Central Hub Terminal', 'Airport Express Link', 'City Center Concourse', 'Government District', 'University Campus', 'General Hospital'].map((s) => (
            <div key={s} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-white">{s}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">Automated signaling locked</div>
              </div>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Nominal
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
