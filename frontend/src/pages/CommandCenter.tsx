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
import api from '../api/client'
import LiveFeedPanel from '../components/LiveFeedPanel'
import SectorMap from '../components/SectorMap'
import StatCard from '../components/StatCard'
import AlertBanner from '../components/AlertBanner'
import {
  Cpu,
  ShieldAlert,
  AlertTriangle,
  Activity,
  Layers,
  Brain,
  ShieldCheck,
  Atom,
  Building2,
  TrendingUp,
  Radio,
  Clock,
} from 'lucide-react'

const MOCK_CHART = Array.from({ length: 12 }, (_, i) => ({
  time: `${i * 2}:00`,
  threats: Math.floor(Math.random() * 8) + 1,
  normal: Math.floor(Math.random() * 200) + 100,
}))

export default function CommandCenter() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/dashboard/command-center')
      .then(r => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
          <span className="text-slate-400 text-xs font-medium tracking-wide">
            Initializing National Cyber Command Center Telemetry...
          </span>
        </div>
      </div>
    )
  }

  const recentAttacks = stats?.recent_attacks || []

  return (
    <div className="pb-8">
      <AlertBanner />

      <div className="p-6 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                National Cyber Command Center
              </h1>
              <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold px-2 py-0.5 rounded-full">
                DEFCON 4
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1">
              Autonomous bio-inspired security grid protecting 500 interconnected IoT nodes across 8 smart city sectors
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
              <span className="text-emerald-300 font-semibold">GRID SYNCHRONIZED</span>
            </div>
          </div>
        </div>

        {/* Primary KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={<Cpu className="w-5 h-5" />}
            value={stats?.devices_online || 487}
            label="Active IoT Nodes"
            color="text-cyan-400"
            pulse
            trend="97.4% online"
          />
          <StatCard
            icon={<ShieldAlert className="w-5 h-5" />}
            value={stats?.attacks_today || 14}
            label="Attacks Neutralized Today"
            color="text-red-400"
            sub="Auto-quarantined & recorded"
          />
          <StatCard
            icon={<AlertTriangle className="w-5 h-5" />}
            value={stats?.critical_alerts || 2}
            label="Active Critical Alerts"
            color="text-orange-400"
            sub="Under active containment"
          />
          <StatCard
            icon={<Activity className="w-5 h-5" />}
            value={`${stats?.system_health || 99.8}%`}
            label="Immune Grid Health"
            color="text-green-400"
            trend="+0.2% vs 24h"
          />
        </div>

        {/* City Sector Topology Grid */}
        <SectorMap />

        {/* Network Traffic & Sector Health Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Traffic Area Chart */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-white">Grid Telemetry Traffic (24h)</h2>
                  <p className="text-[11px] text-slate-400">Normal sensor throughput vs detected attack bursts</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" /> Normal
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-400" /> Attacks
                </span>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={210}>
              <AreaChart data={MOCK_CHART} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="roseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(11, 17, 33, 0.95)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '0.75rem',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
                  }}
                  itemStyle={{ fontSize: 12 }}
                />
                <Area type="monotone" dataKey="normal" stroke="#06b6d4" strokeWidth={2} fill="url(#cyanGrad)" name="Normal Telemetry" />
                <Area type="monotone" dataKey="threats" stroke="#f43f5e" strokeWidth={2} fill="url(#roseGrad)" name="Attack Vectors" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Sector Status Breakdown */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Building2 className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-white">Smart City Sector Health</h2>
                  <p className="text-[11px] text-slate-400">Live operational status and device density</p>
                </div>
              </div>
            </div>

            <div className="space-y-1.5 divide-y divide-white/[0.04]">
              {(stats?.city_sectors || [
                { sector: 'traffic', status: 'normal', devices: 100, threats: 0 },
                { sector: 'hospital', status: 'alert', devices: 80, threats: 1 },
                { sector: 'water', status: 'normal', devices: 60, threats: 0 },
                { sector: 'power', status: 'normal', devices: 80, threats: 0 },
                { sector: 'surveillance', status: 'normal', devices: 80, threats: 0 },
                { sector: 'metro', status: 'normal', devices: 50, threats: 0 },
                { sector: 'airport', status: 'alert', devices: 30, threats: 1 },
                { sector: 'government', status: 'normal', devices: 20, threats: 0 },
              ]).map((s: any) => (
                <div key={s.sector} className="flex items-center justify-between py-2.5 px-2 hover:bg-white/[0.02] rounded-lg transition-colors">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        s.status === 'normal' ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' :
                        s.status === 'alert'  ? 'bg-amber-400 animate-pulse shadow-[0_0_6px_rgba(251,191,36,0.8)]' :
                        'bg-rose-400 shadow-[0_0_6px_rgba(244,63,94,0.8)]'
                      }`}
                    />
                    <span className="capitalize text-xs font-semibold text-white">{s.sector} Sector</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    <span className="font-mono text-slate-400">{s.devices} nodes</span>
                    {s.threats > 0 ? (
                      <span className="badge-high">{s.threats} anomaly</span>
                    ) : (
                      <span className="badge-low">nominal</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Secondary KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={<Layers className="w-5 h-5" />}
            value={stats?.blockchain_blocks?.toLocaleString() || '14,823'}
            label="Immune Blocks Mined"
            color="text-cyan-400"
            sub="Proof-of-Immunity verified"
          />
          <StatCard
            icon={<Brain className="w-5 h-5" />}
            value={stats?.ai_accuracy || '97.2%'}
            label="FAC Model Accuracy"
            color="text-green-400"
            sub="Dual Defender+Attacker FL"
          />
          <StatCard
            icon={<ShieldCheck className="w-5 h-5" />}
            value={stats?.detection_rate || '97.3%'}
            label="Multi-Layer Detection"
            color="text-emerald-400"
            sub="0 False Negatives (PQC+AI)"
          />
          <StatCard
            icon={<Atom className="w-5 h-5" />}
            value={stats?.quantum_checks?.toLocaleString() || '12,450'}
            label="Quantum DNA Checks"
            color="text-purple-400"
            sub="4-Qubit Circuit Encoding"
          />
        </div>

        {/* Recent Attacks & Live Stream Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Attacks */}
          <div className="card">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-white">Recent Attack Containments</h2>
                  <p className="text-[11px] text-slate-400">Neutralized malicious vectors and quarantine actions</p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              {recentAttacks.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No active attacks currently recorded.
                </div>
              ) : (
                recentAttacks.map((a: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] transition-colors">
                    <div className="flex items-center gap-3">
                      <span className="badge-high uppercase text-[10px]">
                        {a.type?.replace('_', ' ')}
                      </span>
                      <span className="text-xs font-medium text-slate-200 capitalize">
                        {a.sector} sector
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {a.time}
                      </span>
                      <span className="badge-low uppercase text-[10px]">{a.status}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Live Feed Stream */}
          <LiveFeedPanel maxEvents={15} />
        </div>
      </div>
    </div>
  )
}
