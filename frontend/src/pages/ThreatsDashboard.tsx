import { useEffect, useState } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'
import {
  ShieldAlert,
  AlertOctagon,
  ShieldCheck,
  Zap,
  TrendingUp,
  PieChart as PieIcon,
  Search,
  Filter,
  Atom,
  Brain,
  Layers,
  Target,
} from 'lucide-react'

const PIE_COLORS = ['#f43f5e', '#fb923c', '#eab308', '#06b6d4', '#818cf8', '#34d399']

const TREND = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  threats: Math.floor(Math.random() * 8 + (i >= 7 && i <= 9 || i >= 17 && i <= 19 ? 5 : 1)),
}))

export default function ThreatsDashboard() {
  const [threats, setThreats] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/threats/').then(r => setThreats(r.data.threats || [])),
      api.get('/api/threats/summary').then(r => setSummary(r.data)),
    ]).finally(() => setLoading(false))

    const id = setInterval(() => {
      api.get('/api/threats/').then(r => setThreats(r.data.threats || [])).catch(() => {})
      api.get('/api/threats/summary').then(r => setSummary(r.data)).catch(() => {})
    }, 6000)
    return () => clearInterval(id)
  }, [])

  const sevBadge = (s: string) => {
    const m: Record<string, string> = {
      critical: 'badge-critical',
      high: 'badge-high',
      medium: 'badge-medium',
      low: 'badge-low',
    }
    return m[s] || 'badge-low'
  }

  const attackCounts = Object.entries(summary?.by_attack_type || {
    spoofing: 28,
    ddos: 15,
    data_poisoning: 12,
    replay_attack: 9,
    mitm: 7,
    ransomware: 5,
  }).map(([name, value]: any) => ({ name: name.replace('_', ' '), value }))

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-rose-500/30 border-t-rose-500 rounded-full animate-spin" />
          <span className="text-slate-400 text-xs font-medium tracking-wide">
            Loading Real-Time Threat Intelligence Telemetry...
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Threat Intelligence Command
            </h1>
            <span className="text-xs bg-rose-500/10 border border-rose-500/20 text-rose-300 font-semibold px-2 py-0.5 rounded-full">
              LIVE RADAR
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Real-time multi-tier attack detection powered by Quantum QBF + AI Brain (FAC) + Immune Blockchain
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
          <span className="w-2 h-2 bg-rose-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.8)]" />
          ACTIVE INTRUSION MONITORING
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<ShieldAlert className="w-5 h-5" />}
          value={summary?.total_today || 14}
          label="Total Threats Detected"
          color="text-red-400"
          pulse
          sub="Last 24 hours"
        />
        <StatCard
          icon={<AlertOctagon className="w-5 h-5" />}
          value={summary?.critical || 2}
          label="Critical Exploits"
          color="text-red-500"
          sub="Instant isolation enacted"
        />
        <StatCard
          icon={<ShieldCheck className="w-5 h-5" />}
          value={summary?.detection_rate || '97.3%'}
          label="Overall Detection Accuracy"
          color="text-green-400"
          trend="+1.2% model gain"
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          value={`${summary?.avg_response_time_ms || 245}ms`}
          label="Avg Neutralization Time"
          color="text-cyan-400"
          sub="Automated zero-trust reaction"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat Frequency Area Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <TrendingUp className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white">Threat Frequency Velocity (24h)</h2>
                <p className="text-[11px] text-slate-400">Hourly attack vector attempts neutralized by defense mesh</p>
              </div>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <AreaChart data={TREND} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
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
                  boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
                }}
              />
              <Area type="monotone" dataKey="threats" stroke="#f43f5e" strokeWidth={2} fill="url(#redGrad)" name="Detected Attacks" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Attack Vector Distribution Pie Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <PieIcon className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white">Attack Vector Distribution</h2>
                <p className="text-[11px] text-slate-400">Categorical classification of incoming exploit payloads</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="w-full sm:w-1/2 h-[190px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={attackCounts}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    dataKey="value"
                    paddingAngle={3}
                  >
                    {attackCounts.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: 'rgba(11, 17, 33, 0.95)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '0.75rem',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="w-full sm:w-1/2 space-y-2">
              {attackCounts.map((a, i) => (
                <div key={a.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                    />
                    <span className="text-slate-300 capitalize">{a.name}</span>
                  </div>
                  <span className="font-mono font-semibold text-white bg-white/[0.04] px-2 py-0.5 rounded">
                    {a.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detection Mechanism Performance */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Search className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Detection Mechanism Performance Matrix</h2>
            <p className="text-[11px] text-slate-400">ImmunoGrid defense layer efficacy across targeted attack classes</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { name: 'Quantum Fingerprint (QBF)', rate: 95.2, attacks: 'Spoofing, MITM, Impostor IDs', icon: Atom, color: 'bg-cyan-500' },
            { name: 'AI Brain Consciousness (FAC)', rate: 91.7, attacks: 'DDoS, Poisoning, Evasion', icon: Brain, color: 'bg-indigo-500' },
            { name: 'Blockchain Immune Memory', rate: 89.4, attacks: 'Replay, Tampering, Rollbacks', icon: Layers, color: 'bg-purple-500' },
            { name: 'Decoy Honeypot Network', rate: 93.0, attacks: 'Ransomware, Zero-Day APTs', icon: Target, color: 'bg-amber-500' },
          ].map((m) => {
            const Icon = m.icon
            return (
              <div key={m.name} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.12] transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-white truncate">{m.name}</span>
                  <Icon className="w-4 h-4 text-slate-400" />
                </div>
                <div className="text-2xl font-bold text-white mb-2 font-mono">
                  {m.rate}%
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full mb-2 overflow-hidden">
                  <div className={`h-full ${m.color} rounded-full transition-all`} style={{ width: `${m.rate}%` }} />
                </div>
                <div className="text-[11px] text-slate-400 truncate">Targets: {m.attacks}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Live Threat Telemetry Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Live Threat Telemetry Feed</h2>
              <p className="text-[11px] text-slate-400">{threats.length} recorded events · Auto-refresh active</p>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-white/[0.08] text-[11px] uppercase tracking-wider">
                <th className="pb-3 pr-4 font-semibold">Severity</th>
                <th className="pb-3 pr-4 font-semibold">Attack Vector</th>
                <th className="pb-3 pr-4 font-semibold">Target Sector</th>
                <th className="pb-3 pr-4 font-semibold">Target Node ID</th>
                <th className="pb-3 pr-4 font-semibold">Detected By</th>
                <th className="pb-3 pr-4 font-semibold">Timestamp</th>
                <th className="pb-3 font-semibold">Action Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {threats.slice(0, 15).map((t: any, i: number) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 pr-4"><span className={sevBadge(t.severity)}>{t.severity}</span></td>
                  <td className="py-3 pr-4 capitalize font-medium text-white">{t.attack_type?.replace(/_/g, ' ')}</td>
                  <td className="py-3 pr-4 capitalize text-slate-300">{t.target_sector} Sector</td>
                  <td className="py-3 pr-4 font-mono text-[11px] text-indigo-400">{t.device_id || 'NODE-001'}</td>
                  <td className="py-3 pr-4 text-slate-400 capitalize">{t.detected_by?.replace(/_/g, ' ')}</td>
                  <td className="py-3 pr-4 text-slate-500 font-mono text-[11px]">{new Date(t.timestamp).toLocaleTimeString()}</td>
                  <td className="py-3"><span className="badge-low uppercase text-[10px]">{t.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
