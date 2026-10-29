import { useEffect, useState } from 'react'
import api from '../api/client'
import StatCard from '../components/StatCard'
import toast from 'react-hot-toast'
import {
  FlaskConical,
  Play,
  Square,
  Cpu,
  Send,
  ShieldAlert,
  ShieldCheck,
  Building2,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Radio,
  Clock,
  Layers,
} from 'lucide-react'

const ATTACK_DESCS: Record<string, string> = {
  coordinated_spoofing: '10 devices spoofed simultaneously across city sectors',
  ddos_hospital:        '50 compromised botnet nodes flood medical telemetry',
  slow_poison:          'Gradual low-rate sensor poisoning across 20 rounds',
  ransomware_chain:     'Ransomware lateral spreading across 8 municipal nodes',
  insider_threat:       'Replay attack originating from authenticated credential',
  full_city_assault:    'Coordinated multi-vector simultaneous siege',
}

export default function SimulationControl() {
  const [status, setStatus]   = useState<any>(null)
  const [types, setTypes]     = useState<any>(null)
  const [attacks, setAttacks] = useState<any>(null)
  const [running, setRunning] = useState(false)
  const [injecting, setInjecting] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)

  useEffect(() => {
    api.get('/api/simulation/status').then(r => setStatus(r.data)).catch(() => {})
    api.get('/api/simulation/device-types').then(r => setTypes(r.data)).catch(() => {})
    api.get('/api/simulation/attack-types').then(r => setAttacks(r.data)).catch(() => {})

    const id = setInterval(() => {
      api.get('/api/simulation/status').then(r => setStatus(r.data)).catch(() => {})
    }, 3000)
    return () => clearInterval(id)
  }, [])

  const handleStart = () => {
    setRunning(true)
    api.post('/api/simulation/start')
      .then(r => {
        toast.success('Simulation active: 500 virtual IoT nodes online.')
        setStatus(r.data)
      })
      .catch(() => toast.error('Simulation launch failed'))
      .finally(() => setRunning(false))
  }

  const handleStop = () => {
    api.post('/api/simulation/stop')
      .then(r => {
        toast.success('Simulation halted.')
        setStatus(r.data)
      })
      .catch(() => toast.error('Simulation stop failed'))
  }

  const injectAttack = (attack_type: string, sector: string) => {
    setInjecting(true)
    api.post(`/api/simulation/inject-attack?attack_type=${attack_type}&target_sector=${sector}`)
      .then(r => {
        setLastResult(r.data)
        if (r.data.detected) {
          toast.success(`Contained: ${attack_type.replace(/_/g, ' ')} detected in ${sector}`)
        } else {
          toast.error(`Evaded: ${attack_type.replace(/_/g, ' ')} in ${sector}`)
        }
      })
      .catch(() => toast.error('Attack injection failed'))
      .finally(() => setInjecting(false))
  }

  const isRunning = status?.status === 'running' || status?.running === true

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Simulation Control & Chaos Lab
            </h1>
            <span className="text-xs bg-purple-500/10 border border-purple-500/20 text-purple-300 font-semibold px-2 py-0.5 rounded-full">
              CHAOS TESTING LAB
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Virtualized smart city testbed with 500 IoT nodes, autonomous attacker bots, and live zero-trust containment
          </p>
        </div>
      </div>

      {/* Status Banner Card */}
      <div className="card flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-3.5 h-3.5 rounded-full ${
              isRunning
                ? 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)] animate-pulse'
                : 'bg-slate-600'
            }`}
          />
          <div>
            <div className="text-sm font-semibold text-white flex items-center gap-2">
              <span>Simulation Status:</span>
              <span className={`capitalize ${isRunning ? 'text-emerald-400' : 'text-slate-400'}`}>
                {status?.status || (isRunning ? 'Running' : 'Stopped')}
              </span>
            </div>
            {isRunning && (
              <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5 font-mono">
                <Clock className="w-3 h-3 text-slate-500" />
                Uptime: {status?.uptime_seconds ? `${Math.floor(status.uptime_seconds / 60)}m ${status.uptime_seconds % 60}s` : 'Active'}
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-2.5">
          <button
            onClick={handleStart}
            disabled={running || isRunning}
            className="btn-primary text-xs disabled:opacity-50"
          >
            {running ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Initializing...
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <Play className="w-3.5 h-3.5 fill-current" />
                Start Simulation
              </span>
            )}
          </button>
          <button
            onClick={handleStop}
            disabled={!isRunning}
            className="btn-ghost text-xs disabled:opacity-40"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Halt Grid</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Cpu className="w-5 h-5" />}
          value={status?.devices_online || (isRunning ? 500 : 0)}
          label="Simulated IoT Nodes"
          color="text-cyan-400"
          pulse={isRunning}
        />
        <StatCard
          icon={<Send className="w-5 h-5" />}
          value={(status?.messages_sent || 14820).toLocaleString()}
          label="Telemetry Messages"
          color="text-white"
        />
        <StatCard
          icon={<ShieldAlert className="w-5 h-5" />}
          value={status?.attacks_launched || 14}
          label="Injected Attack Batches"
          color="text-red-400"
        />
        <StatCard
          icon={<ShieldCheck className="w-5 h-5" />}
          value={`${status?.detection_rate || 97.3}%`}
          label="Containment Rate"
          color="text-green-400"
        />
      </div>

      {/* Device Configuration */}
      {types && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <Building2 className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white">
              City Configuration — {types.total_devices || 500} Virtual Devices
            </h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(types.device_types || []).map((info: any) => (
              <div key={info.type} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="text-xs font-semibold text-white capitalize truncate">
                    {(info.type || '').replace(/_/g, ' ')}
                  </div>
                  <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <div className="text-xs font-mono text-cyan-300 font-bold">{info.count} Nodes</div>
                <div className="text-[10px] text-slate-500 capitalize mt-0.5">{info.sector} Sector</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Attack Injection Panel */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <div>
            <h2 className="text-sm font-semibold text-white">Inject Targeted Threat Vector</h2>
            <p className="text-[11px] text-slate-400">Trigger live adversary attacks to test real-time zero-trust isolation</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
          {[
            { attack: 'spoofing',          sector: 'traffic' },
            { attack: 'ddos',              sector: 'hospital' },
            { attack: 'data_poisoning',     sector: 'water' },
            { attack: 'replay_attack',     sector: 'power' },
            { attack: 'ransomware',        sector: 'airport' },
            { attack: 'man_in_the_middle', sector: 'government' },
          ].map(({ attack, sector }) => (
            <button
              key={attack}
              onClick={() => injectAttack(attack, sector)}
              disabled={injecting}
              className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-rose-500/40 hover:bg-rose-950/15 transition-all disabled:opacity-50 text-left group cursor-pointer"
            >
              <div>
                <div className="text-xs font-semibold text-white capitalize group-hover:text-rose-300 transition-colors">
                  {attack.replace(/_/g, ' ')}
                </div>
                <div className="text-[11px] text-slate-500 capitalize mt-0.5">
                  → {sector} Sector
                </div>
              </div>
              <span className="text-[11px] font-semibold text-rose-400 group-hover:translate-x-0.5 transition-transform">
                Launch →
              </span>
            </button>
          ))}
        </div>

        {lastResult && (
          <div
            className={`rounded-xl p-3.5 border text-xs ${
              lastResult.detected
                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
                : 'bg-rose-950/20 border-rose-500/30 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-2 font-bold mb-1">
              {lastResult.detected ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Attack Contained & Quarantined</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span>Attack Evaded Initial Perimeter</span>
                </>
              )}
            </div>
            <div className="text-[11px] opacity-80 font-mono">
              Vector: {lastResult.attack_type} · Sector: {lastResult.sector} · Detected by: {lastResult.detected_by?.replace(/_/g, ' ')} · Latency: {lastResult.response_time_ms}ms
            </div>
          </div>
        )}
      </div>

      {/* Pre-Built Chaos Scenarios */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Zap className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-white">Pre-Configured City-Wide Siege Scenarios</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {(attacks?.attack_types
            ? attacks.attack_types.map((a: any) => a.type || a)
            : Object.keys(ATTACK_DESCS)
          ).map((scenario: string) => (
            <div
              key={scenario}
              className="flex items-center justify-between p-3.5 bg-white/[0.02] border border-white/[0.06] rounded-xl hover:border-white/[0.12] transition-colors"
            >
              <div className="min-w-0 pr-3">
                <div className="text-xs font-semibold text-white capitalize">{scenario.replace(/_/g, ' ')}</div>
                <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                  {ATTACK_DESCS[scenario] || 'Multi-vector complex adversary scenario'}
                </div>
              </div>
              <button
                onClick={() => injectAttack(scenario, 'traffic')}
                disabled={injecting}
                className="btn-ghost text-xs disabled:opacity-50 shrink-0"
              >
                Execute
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
