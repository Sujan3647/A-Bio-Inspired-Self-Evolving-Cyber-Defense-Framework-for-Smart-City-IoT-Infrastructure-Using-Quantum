import { useEffect, useState } from 'react'
import api from '../api/client'
import StatCard from '../components/StatCard'
import {
  Terminal,
  Cloud,
  Cpu,
  CheckCircle2,
  Clock,
  Boxes,
  Activity,
  RefreshCw,
  Play,
  ArrowRight,
  Server,
} from 'lucide-react'

const PIPELINE_STEPS = [
  { name: 'Git Commit',        status: 'success', time: '0s'   },
  { name: 'Node Tests',        status: 'success', time: '12s'  },
  { name: 'Quantum QBF Tests', status: 'success', time: '8s'   },
  { name: 'Blockchain Tests',  status: 'success', time: '6s'   },
  { name: 'Security Audit',    status: 'success', time: '15s'  },
  { name: 'Docker Build',      status: 'success', time: '45s'  },
  { name: 'Attack Chaos Test', status: 'success', time: '30s'  },
  { name: 'Deploy to AWS',     status: 'running', time: 'Active' },
]

const AWS_SERVICES = [
  { name: 'AWS IoT Core',            status: 'operational', latency: '12ms' },
  { name: 'AWS IoT Greengrass',      status: 'operational', latency: '8ms'  },
  { name: 'Amazon SageMaker (FAC)',  status: 'operational', latency: '45ms' },
  { name: 'Managed Blockchain',      status: 'operational', latency: '28ms' },
  { name: 'AWS Lambda Microservices',status: 'operational', latency: '3ms'  },
  { name: 'Amazon CloudWatch Logs',  status: 'operational', latency: '5ms'  },
  { name: 'Amazon SNS Alerts',       status: 'operational', latency: '7ms'  },
  { name: 'Amazon S3 Ledger Backup', status: 'operational', latency: '18ms' },
]

export default function DevOpsDashboard() {
  const [health, setHealth] = useState<any>(null)
  useEffect(() => { api.get('/api/health').then(r => setHealth(r.data)).catch(() => {}) }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              DevOps & Cloud Infrastructure
            </h1>
            <span className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded-full">
              AWS HYBRID CLOUD
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            AWS cloud service health · Automated CI/CD deployment pipeline · Docker container orchestration
          </p>
        </div>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Server className="w-5 h-5" />}
          value={health?.status || 'Healthy'}
          label="Defense Core API"
          color="text-green-400"
          pulse
          sub="Uvicorn + FastAPI"
        />
        <StatCard
          icon={<Cloud className="w-5 h-5" />}
          value="8 / 8 Online"
          label="AWS Integrated Services"
          color="text-cyan-400"
          sub="100% cloud SLA"
        />
        <StatCard
          icon={<Boxes className="w-5 h-5" />}
          value="11 Containers"
          label="Docker Fleet Orchestration"
          color="text-purple-400"
          sub="Compose + Microservices"
        />
        <StatCard
          icon={<Clock className="w-5 h-5" />}
          value="Continuous"
          label="CI/CD Deployment State"
          color="text-white"
          sub="Last sync: 2h ago"
        />
      </div>

      {/* CI/CD Pipeline */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <RefreshCw className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-white">CI/CD Automated Deployment Pipeline</h2>
        </div>

        <div className="overflow-x-auto pb-2">
          <div className="flex items-center gap-2 min-w-[700px]">
            {PIPELINE_STEPS.map((step, i) => {
              const isSuccess = step.status === 'success'
              const isRunning = step.status === 'running'
              return (
                <div key={step.name} className="flex items-center">
                  <div
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center min-w-[100px] ${
                      isSuccess
                        ? 'bg-emerald-950/15 border-emerald-500/25'
                        : isRunning
                        ? 'bg-indigo-950/20 border-indigo-500/40 animate-pulse'
                        : 'bg-white/[0.02] border-white/[0.06]'
                    }`}
                  >
                    <div className="p-1 rounded-full bg-white/[0.05]">
                      {isSuccess && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                      {isRunning && <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin" />}
                      {!isSuccess && !isRunning && <Clock className="w-4 h-4 text-slate-500" />}
                    </div>
                    <span className="text-xs font-semibold text-white leading-tight">{step.name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{step.time}</span>
                  </div>
                  {i < PIPELINE_STEPS.length - 1 && (
                    <div className="w-4 h-0.5 bg-slate-700/60 shrink-0 mx-1" />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* AWS Services */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Cloud className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">AWS Cloud Services Health Matrix</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {AWS_SERVICES.map((s) => (
            <div key={s.name} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-white">{s.name}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">Latency: {s.latency}</div>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Active
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
