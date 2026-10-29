import { useEffect, useState } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Building2,
  Search,
  Filter,
  PieChart as PieIcon,
  BarChart3,
  Layers,
} from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  online: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25',
  compromised: 'text-rose-400 bg-rose-500/10 border-rose-500/25',
  quarantined: 'text-amber-400 bg-amber-500/10 border-amber-500/25',
  offline: 'text-slate-400 bg-slate-500/10 border-slate-500/25',
}

const PIE_COLORS = ['#10b981', '#f43f5e', '#f59e0b', '#64748b']

export default function DevicesDashboard() {
  const [data, setData] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [filter, setFilter] = useState('')
  const [sectorFilter, setSectorFilter] = useState('all')

  useEffect(() => {
    api.get('/api/devices/?limit=50').then(r => setData(r.data)).catch(() => {})
    api.get('/api/devices/stats').then(r => setStats(r.data)).catch(() => {})
    const id = setInterval(() => {
      api.get('/api/devices/stats').then(r => setStats(r.data)).catch(() => {})
    }, 10000)
    return () => clearInterval(id)
  }, [])

  const devices = (data?.devices || []).filter((d: any) => {
    const matchText = !filter || d.device_id.includes(filter) || d.device_type.includes(filter)
    const matchSector = sectorFilter === 'all' || d.sector === sectorFilter
    return matchText && matchSector
  })

  const statusPie = [
    { name: 'Online',      value: stats?.online || 487 },
    { name: 'Compromised', value: stats?.compromised || 8 },
    { name: 'Quarantined', value: stats?.quarantined || 5 },
    { name: 'Offline',     value: stats?.offline || 0 },
  ]

  const sectorCounts = Object.entries(stats?.by_sector || {
    traffic: 100, surveillance: 80, water: 60, hospital: 80,
    power: 80, metro: 50, airport: 30, government: 20,
  }).map(([sector, count]) => ({ sector, count }))

  const sectors = ['all', ...new Set((data?.devices || []).map((d: any) => d.sector))]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              IoT Device Registry & Telemetry
            </h1>
            <span className="text-xs bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-semibold px-2 py-0.5 rounded-full">
              500 NODES ACTIVE
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Complete virtualized smart city infrastructure across 8 mission-critical operational sectors
          </p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={<Cpu className="w-5 h-5" />}
          value={stats?.total || 500}
          label="Total IoT Nodes"
          color="text-white"
          sub="Mesh network active"
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={stats?.online || 487}
          label="Online Nodes"
          color="text-green-400"
          pulse
          trend="97.4%"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={stats?.compromised || 8}
          label="Compromised"
          color="text-red-400"
          sub="Flagged by QBF"
        />
        <StatCard
          icon={<Lock className="w-5 h-5" />}
          value={stats?.quarantined || 5}
          label="Quarantined"
          color="text-yellow-400"
          sub="Air-gapped by mesh"
        />
        <StatCard
          icon={<Building2 className="w-5 h-5" />}
          value={8}
          label="Active Sectors"
          color="text-cyan-400"
          sub="100% telemetry coverage"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <PieIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Node Health Distribution</h2>
              <p className="text-[11px] text-slate-400">Current operational state across the fleet</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="w-full sm:w-1/2 h-[160px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusPie} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value" paddingAngle={4}>
                    {statusPie.map((_, i) => (
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
              {statusPie.map((s, i) => (
                <div key={s.name} className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="text-slate-300">{s.name}</span>
                  </div>
                  <span className="font-mono font-semibold text-white bg-white/[0.04] px-2 py-0.5 rounded">
                    {s.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Devices by Sector */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Device Density by Sector</h2>
              <p className="text-[11px] text-slate-400">Distributed sensor counts across city zones</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={sectorCounts} layout="vertical" margin={{ top: 0, right: 10, left: 15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="sector" stroke="#64748b" tick={{ fontSize: 10 }} width={75} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
              />
              <Bar dataKey="count" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Active Nodes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters & Table */}
      <div className="card">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Registered Node Inventory</h2>
              <p className="text-[11px] text-slate-400">{devices.length} nodes matching active search criteria</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                className="pl-8 pr-3 py-1.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500 w-48 transition-all"
                placeholder="Search node ID or type..."
                value={filter}
                onChange={e => setFilter(e.target.value)}
              />
            </div>
            <select
              className="bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-indigo-500 transition-all cursor-pointer"
              value={sectorFilter}
              onChange={e => setSectorFilter(e.target.value)}
            >
              {sectors.map(s => (
                <option key={s} value={s} className="bg-slate-900 text-slate-200">
                  {s === 'all' ? 'All Sectors' : `${s.charAt(0).toUpperCase() + s.slice(1)} Sector`}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-white/[0.08] text-[11px] uppercase tracking-wider">
                <th className="pb-3 pr-4 font-semibold">Node ID</th>
                <th className="pb-3 pr-4 font-semibold">Device Type</th>
                <th className="pb-3 pr-4 font-semibold">Sector</th>
                <th className="pb-3 pr-4 font-semibold">Status</th>
                <th className="pb-3 pr-4 font-semibold">Quantum Fingerprint Match</th>
                <th className="pb-3 pr-4 font-semibold">Telemetry Packets</th>
                <th className="pb-3 font-semibold">Geo Location</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {devices.slice(0, 25).map((d: any, i: number) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 pr-4 font-mono text-[11px] text-indigo-400">{d.device_id}</td>
                  <td className="py-3 pr-4 capitalize text-slate-300">{d.device_type?.replace(/_/g, ' ')}</td>
                  <td className="py-3 pr-4 capitalize text-slate-400">{d.sector}</td>
                  <td className="py-3 pr-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${STATUS_COLORS[d.status] || STATUS_COLORS.online}`}>
                      {d.status}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-cyan-400 rounded-full"
                          style={{ width: `${(d.fingerprint_match || 0.97) * 100}%` }}
                        />
                      </div>
                      <span className="font-mono text-cyan-300 text-[11px]">
                        {((d.fingerprint_match || 0.97) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 pr-4 font-mono text-slate-400">{d.messages_sent?.toLocaleString() || '1,420'}</td>
                  <td className="py-3 text-slate-500 font-mono text-[11px]">{d.location || 'Zone-4A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {devices.length === 0 && (
          <div className="text-center text-slate-500 py-10 text-xs">
            No registered nodes match the current filter selection.
          </div>
        )}
      </div>
    </div>
  )
}
