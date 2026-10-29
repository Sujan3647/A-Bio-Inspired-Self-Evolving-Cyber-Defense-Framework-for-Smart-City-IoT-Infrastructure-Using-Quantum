import { useEffect, useState } from 'react'
import {
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
import toast from 'react-hot-toast'
import {
  Target,
  ShieldAlert,
  Brain,
  BarChart3,
  Plus,
  Radio,
  FileText,
  Sparkles,
  Zap,
  CheckCircle2,
} from 'lucide-react'

export default function HoneypotDashboard() {
  const [stats, setStats]   = useState<any>(null)
  const [active, setActive] = useState<any[]>([])
  const [intel, setIntel]   = useState<any[]>([])
  const [spawning, setSpawning] = useState(false)

  const fetchAll = () => {
    api.get('/api/honeypot/stats').then(r => setStats(r.data)).catch(() => {})
    api.get('/api/honeypot/active').then(r => setActive(r.data.honeypots || [])).catch(() => {})
    api.get('/api/honeypot/intelligence').then(r => setIntel(r.data.reports || [])).catch(() => {})
  }

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 8000)
    return () => clearInterval(id)
  }, [])

  const handleSpawn = (sector: string) => {
    setSpawning(true)
    api.post(`/api/honeypot/spawn?sector=${sector}&count=3`)
      .then(r => {
        toast.success(`Spawned ${r.data.spawned || 3} dynamic decoy traps in ${sector} sector`)
        fetchAll()
      })
      .catch(() => toast.error('Honeypot spawn failed'))
      .finally(() => setSpawning(false))
  }

  const attackDist = [
    { type: 'Spoofing',   count: stats?.by_attack?.spoofing || 28 },
    { type: 'DDoS',       count: stats?.by_attack?.ddos || 15 },
    { type: 'MITM',       count: stats?.by_attack?.mitm || 12 },
    { type: 'Ransomware', count: stats?.by_attack?.ransomware || 9 },
    { type: 'Replay',     count: stats?.by_attack?.replay || 7 },
    { type: 'Poisoning',  count: stats?.by_attack?.poisoning || 5 },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Honeypot Decoy Trap Mesh
            </h1>
            <span className="text-xs bg-amber-500/10 border border-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded-full">
              BIO-MIMETIC DECOYS
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Artificial white blood cells of the smart city — autonomous traps that lure, analyze, and reverse-engineer adversary payloads
          </p>
        </div>
        <button
          onClick={() => handleSpawn('traffic')}
          disabled={spawning}
          className="btn-primary text-xs disabled:opacity-50"
        >
          {spawning ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Deploying Decoys...
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" />
              Spawn Decoy Cluster
            </span>
          )}
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Target className="w-5 h-5" />}
          value={stats?.active_honeypots || 23}
          label="Active Decoy Traps"
          color="text-yellow-400"
          pulse
          trend="23 active nodes"
        />
        <StatCard
          icon={<ShieldAlert className="w-5 h-5" />}
          value={stats?.attackers_trapped || 7}
          label="Adversaries Trapped"
          color="text-red-400"
          sub="Isolated in sandbox"
        />
        <StatCard
          icon={<BarChart3 className="w-5 h-5" />}
          value={(stats?.total_interactions || 142).toLocaleString()}
          label="Telemetry Interactions"
          color="text-cyan-400"
          sub="Deep packet analysis"
        />
        <StatCard
          icon={<Brain className="w-5 h-5" />}
          value={stats?.ai_samples_generated || 1204}
          label="AI Defense Training Sets"
          color="text-purple-400"
          sub="Fed directly to FAC"
        />
      </div>

      {/* Captured Types & Active Traps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Captured Attacks Bar Chart */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Captured Attack Vectors</h2>
              <p className="text-[11px] text-slate-400">Payload volume intercepted across honeypot sensors</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={210}>
            <BarChart data={attackDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="type" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(11, 17, 33, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                }}
              />
              <Bar dataKey="count" fill="#f59e0b" name="Captured Payloads" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Active Honeypot Nodes */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Active Bio-Mimetic Decoy Nodes</h2>
              <p className="text-[11px] text-slate-400">Synthetic devices broadcasting realistic IoT sensor profiles</p>
            </div>
          </div>

          <div className="space-y-2 max-h-56 overflow-y-auto divide-y divide-white/[0.04]">
            {(active.length > 0 ? active : Array.from({ length: 6 }, (_, i) => ({
              honeypot_id: `trap-${Math.random().toString(16).slice(2, 10)}`,
              mimics_device_id: `${['traffic','hospital','water','power'][i % 4]}-sensor-${String(i + 1).padStart(3, '0')}`,
              mimics_sector: ['traffic','hospital','water','power','metro','airport'][i % 6],
              interactions: Math.floor(Math.random() * 20),
            }))).map((hp: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2 text-xs">
                <div>
                  <span className="font-mono text-indigo-400 text-[11px] font-semibold">{hp.honeypot_id?.slice(0, 20)}</span>
                  <div className="text-[10px] text-slate-500 mt-0.5">Emulates: {hp.mimics_device_id}</div>
                </div>
                <div className="text-right">
                  <span className="badge-low uppercase text-[10px] capitalize">{hp.mimics_sector}</span>
                  {hp.interactions > 0 && (
                    <div className="text-amber-400 text-[11px] font-mono mt-0.5">{hp.interactions} Trapped Probes</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Intelligence Reports */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Decoy Forensic Intelligence Dossiers</h2>
            <p className="text-[11px] text-slate-400">Extracted behavioral signatures converted into antibodies for model training</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(intel.length > 0 ? intel : Array.from({ length: 4 }, (_, i) => ({
            report_id: `INTEL-${Math.random().toString(16).slice(2, 10).toUpperCase()}`,
            attacker_profile: {
              attacker_id: `threat-actor-alpha-${i + 1}`,
              attack_types: [['spoofing','ddos','mitm','ransomware'][i % 4]],
              total_attempts: Math.floor(Math.random() * 15) + 3,
            },
            recommended_defenses: [
              'Elevate quantum fingerprint threshold to 0.95',
              'Deploy 3 additional decoy nodes in sector perimeter',
            ],
            ai_training_samples: Math.floor(Math.random() * 20) + 12,
            generated_at: new Date(Date.now() - i * 7200000).toISOString(),
          }))).slice(0, 4).map((report: any, i: number) => (
            <div key={i} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] text-xs space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-white/[0.04]">
                <span className="font-mono text-indigo-400 font-bold">{report.report_id}</span>
                <span className="text-purple-300 font-mono">{report.ai_training_samples} Synthetic Datasets</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-white font-semibold">{report.attacker_profile?.attacker_id}</span>
                {report.attacker_profile?.attack_types?.map((t: string) => (
                  <span key={t} className="badge-medium uppercase text-[10px]">{t.replace(/_/g, ' ')}</span>
                ))}
              </div>
              <div className="space-y-1 text-slate-400 text-[11px]">
                {(report.recommended_defenses || []).map((d: string, j: number) => (
                  <div key={j} className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-cyan-400 shrink-0" />
                    <span>{d}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sector Quick-Spawn Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <Zap className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-semibold text-white">Deploy Traps by City Sector</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {['traffic','hospital','water','power','metro','airport'].map((sector) => (
              <button
                key={sector}
                onClick={() => handleSpawn(sector)}
                disabled={spawning}
                className="btn-ghost text-xs capitalize disabled:opacity-50 hover:border-amber-500/40 hover:text-amber-300"
              >
                + {sector} Sector
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Bio-Inspired Immune Architecture</h2>
          </div>
          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span>Decoy Honeypots = <strong className="text-white">Artificial White Blood Cells</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Attacker Profiles = <strong className="text-white">Pathogen Behavioral DNA</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              <span>AI Training Samples = <strong className="text-white">Active Cellular Antibodies</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Blockchain Attestation = <strong className="text-white">Permanent Immune Memory</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
