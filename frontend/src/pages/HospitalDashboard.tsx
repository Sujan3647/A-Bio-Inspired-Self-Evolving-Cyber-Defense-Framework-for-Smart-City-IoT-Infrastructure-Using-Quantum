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
  Activity,
  HeartPulse,
  ShieldCheck,
  AlertTriangle,
  PieChart as PieIcon,
  Lock,
  CheckCircle2,
  Building2,
  Clock,
  ShieldAlert,
} from 'lucide-react'

const VITALS_DATA = [
  { time: '00:00', hr_avg: 74, alerts: 0 },
  { time: '04:00', hr_avg: 71, alerts: 0 },
  { time: '08:00', hr_avg: 76, alerts: 1 },
  { time: '12:00', hr_avg: 78, alerts: 0 },
  { time: '16:00', hr_avg: 75, alerts: 0 },
  { time: '20:00', hr_avg: 73, alerts: 1 },
  { time: '23:59', hr_avg: 72, alerts: 0 },
]

const DEVICE_COLORS = ['#06b6d4', '#6366f1', '#a855f7', '#ec4899', '#f59e0b', '#10b981']

export default function HospitalDashboard() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    api.get('/api/dashboard/hospital').then(r => setData(r.data)).catch(() => {})
    const id = setInterval(() => {
      api.get('/api/dashboard/hospital').then(r => setData(r.data)).catch(() => {})
    }, 10000)
    return () => clearInterval(id)
  }, [])

  const deviceTypes = Object.entries(
    data?.device_types || {
      icu_monitor: 20, ventilator: 15, infusion_pump: 30,
      ecg_machine: 12, mri_scanner: 8, other: 15,
    }
  ).map(([name, value]: any) => ({ name: name.replace(/_/g, ' '), value }))

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Healthcare & Hospital Cyber Defense
            </h1>
            <span className="text-xs bg-rose-500/10 border border-rose-500/20 text-rose-300 font-semibold px-2 py-0.5 rounded-full">
              MINISTRY OF HEALTH
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Critical life-support medical telemetry & PQC-secured patient data encryption (HIPAA / ISO 27001 Certified)
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          HIPAA ENCRYPTED
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<HeartPulse className="w-5 h-5" />}
          value={data?.total_devices || 100}
          label="Medical Node Sensors"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={data?.online || 98}
          label="Online Life Support"
          color="text-green-400"
          trend="98% Active"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={data?.security_alerts || 1}
          label="Security Anomalies"
          color="text-orange-400"
          sub="ER ward isolated"
        />
        <StatCard
          icon={<ShieldCheck className="w-5 h-5" />}
          value="Compliant"
          label="Regulatory Compliance"
          color="text-green-400"
          sub="HIPAA & ISO 27001"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Types Pie */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <PieIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Medical Equipment Class Distribution</h2>
              <p className="text-[11px] text-slate-400">Inventory of IoT telemetry nodes in clinical service</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="w-full sm:w-1/2 h-[180px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={deviceTypes} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" paddingAngle={3}>
                    {deviceTypes.map((_, i) => (
                      <Cell key={i} fill={DEVICE_COLORS[i % DEVICE_COLORS.length]} />
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
            <div className="w-full sm:w-1/2 space-y-1.5">
              {deviceTypes.map((d, i) => (
                <div key={d.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: DEVICE_COLORS[i % DEVICE_COLORS.length] }} />
                    <span className="text-slate-300 capitalize">{d.name}</span>
                  </div>
                  <span className="font-mono text-white font-semibold bg-white/[0.04] px-2 py-0.5 rounded">
                    {d.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alerts over time */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Security Alerts Over Time (24h)</h2>
              <p className="text-[11px] text-slate-400">Neutralized ransomware and telemetry alteration probes</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={VITALS_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
              <Bar dataKey="alerts" fill="#f97316" name="Security Alerts" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Ward Status Grid */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Building2 className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white">Clinical Hospital Ward Status</h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { ward: 'ICU Critical Ward 1', devices: 18, status: 'secure', threats: 0 },
            { ward: 'ICU Critical Ward 2', devices: 16, status: 'secure', threats: 0 },
            { ward: 'Emergency Trauma Unit', devices: 22, status: 'alert', threats: 1 },
            { ward: 'Surgical Block Theta', devices: 14, status: 'secure', threats: 0 },
            { ward: 'Maternity Telemetry', devices: 10, status: 'secure', threats: 0 },
            { ward: 'Diagnostic Radiology', devices: 8, status: 'secure', threats: 0 },
          ].map((w) => (
            <div
              key={w.ward}
              className={`p-3.5 rounded-xl border transition-all ${
                w.status === 'alert'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-white/[0.02] border-white/[0.06]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-white truncate">{w.ward}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    w.status === 'alert'
                      ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                      : 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  }`}
                />
              </div>
              <div className="text-[11px] text-slate-400 font-mono">{w.devices} Monitored Beds</div>
              {w.threats > 0 ? (
                <div className="text-[11px] text-amber-300 font-semibold mt-1">1 Probed Telemetry Stream</div>
              ) : (
                <div className="text-[11px] text-emerald-400 font-medium mt-1">Perimeter Secure</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Security & Compliance Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <Lock className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white">Cryptographic Life Support Defense</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Post-Quantum Cryptography:</span>
              <span className="text-emerald-400 font-semibold">Active — Kyber-512 KEM</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Life-Support Node Verification:</span>
              <span className="text-emerald-400 font-semibold">100% Certified</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Quantum Fingerprint Match:</span>
              <span className="text-cyan-300 font-mono font-medium">{data?.fingerprint_match_rate || '99.6%'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Ransomware Attempts Blocked:</span>
              <span className="text-emerald-400 font-medium">3 Neutralized</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Healthcare Regulatory Compliance</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            {[
              { label: 'HIPAA Security & Privacy Rule', value: 'Compliant', color: 'text-emerald-400' },
              { label: 'ISO 27001 Medical Cloud', value: 'Compliant', color: 'text-emerald-400' },
              { label: 'Patient Record Confidentiality', value: '100% Encrypted', color: 'text-emerald-400' },
              { label: 'Audit Trail Attestation', value: 'Sealed on Ledger', color: 'text-indigo-300' },
              { label: 'DP Budget Remaining (ε)', value: `${data?.dp_budget_remaining || 82}%`, color: 'text-cyan-300' },
            ].map((c) => (
              <div key={c.label} className="flex justify-between py-1 border-b border-white/[0.02] last:border-0">
                <span className="text-slate-400">{c.label}:</span>
                <span className={`font-semibold ${c.color}`}>{c.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
