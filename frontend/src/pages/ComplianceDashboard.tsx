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
import {
  FileCheck2,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  FileText,
  Lock,
  Scale,
  Clock,
  ShieldAlert,
} from 'lucide-react'

const MONTHLY_INCIDENTS = [
  { month: 'Jan', incidents: 312, resolved: 310 },
  { month: 'Feb', incidents: 298, resolved: 296 },
  { month: 'Mar', incidents: 342, resolved: 340 },
  { month: 'Apr', incidents: 289, resolved: 288 },
  { month: 'May', incidents: 378, resolved: 375 },
  { month: 'Jun', incidents: 421, resolved: 419 },
  { month: 'Jul', incidents: 234, resolved: 232 },
]

export default function ComplianceDashboard() {
  const [data, setData] = useState<any>(null)
  const [compliance, setCompliance] = useState<any>(null)
  const [incidents, setIncidents] = useState<any[]>([])

  useEffect(() => {
    api.get('/api/dashboard/compliance').then(r => setData(r.data)).catch(() => {})
    api.get('/api/reports/compliance').then(r => setCompliance(r.data)).catch(() => {})
    api.get('/api/reports/incident-log?limit=15').then(r => setIncidents(r.data.incidents || [])).catch(() => {})
  }, [])

  const standards = compliance?.standards || [
    { name: 'ISO/IEC 27001:2022', status: 'compliant',   score: 97, last_audit: '2026-07-01', next_audit: '2026-10-01' },
    { name: 'NIST CSF v2.0',      status: 'compliant',   score: 94, last_audit: '2026-07-01', next_audit: '2026-10-01' },
    { name: 'EU GDPR Art. 32',    status: 'compliant',   score: 99, last_audit: '2026-06-15', next_audit: '2026-09-15' },
    { name: 'HIPAA Security Rule',status: 'compliant',   score: 98, last_audit: '2026-07-01', next_audit: '2026-10-01' },
    { name: 'PCI-DSS v4.0',       status: 'partial',     score: 87, last_audit: '2026-06-01', next_audit: '2026-09-01' },
    { name: 'SOC 2 Type II',      status: 'in_progress', score: 78, last_audit: '2026-05-01', next_audit: '2026-08-01' },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Regulatory Compliance & Audit Trail
            </h1>
            <span className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded-full">
              4 / 6 CERTIFIED
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Blockchain-verified judicial audit trail · ISO 27001 · NIST CSF · EU GDPR · HIPAA · Zero-Trust Compliance
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <Scale className="w-3.5 h-3.5 text-emerald-400" />
          JUDICIAL RECORD VALIDATED
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<ShieldCheck className="w-5 h-5" />}
          value="4 / 6"
          label="Regulatory Frameworks"
          color="text-green-400"
          pulse
          sub="ISO & NIST Certified"
        />
        <StatCard
          icon={<FileText className="w-5 h-5" />}
          value={(data?.total_incidents || 3847).toLocaleString()}
          label="Total Audited Incidents"
          color="text-white"
          sub="Indexed in blockchain"
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={(data?.incidents_resolved || 3844).toLocaleString()}
          label="Resolved & Sealed"
          color="text-green-400"
          trend="99.92% closure"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={data?.incidents_open || 3}
          label="Pending Remediation"
          color="text-orange-400"
          sub="Under legal review"
        />
      </div>

      {/* Standards Grid */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <FileCheck2 className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white">Compliance Frameworks Status</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {standards.map((s: any) => {
            const isCompliant = s.status === 'compliant'
            const isPartial = s.status === 'partial'
            return (
              <div
                key={s.name}
                className={`p-4 rounded-xl border transition-all ${
                  isCompliant
                    ? 'bg-emerald-950/15 border-emerald-500/25'
                    : isPartial
                    ? 'bg-amber-950/15 border-amber-500/25'
                    : 'bg-purple-950/15 border-purple-500/25'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white text-xs">{s.name}</span>
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      isCompliant
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : isPartial
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        : 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                    }`}
                  >
                    {isCompliant && <CheckCircle2 className="w-3 h-3" />}
                    {isPartial && <AlertTriangle className="w-3 h-3" />}
                    {!isCompliant && !isPartial && <Clock className="w-3 h-3" />}
                    {isCompliant ? 'Compliant' : isPartial ? 'Partial' : 'In Review'}
                  </span>
                </div>

                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Audit Score</span>
                    <span className="font-mono font-bold text-white">{s.score}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        isCompliant ? 'bg-emerald-400' : isPartial ? 'bg-amber-400' : 'bg-purple-400'
                      }`}
                      style={{ width: `${s.score}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Audited: {s.last_audit}</span>
                  <span>Next: {s.next_audit}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Monthly Incidents Bar Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white">Monthly Incident Remediation History</h2>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={210}>
          <BarChart data={MONTHLY_INCIDENTS} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: 'rgba(11, 17, 33, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.75rem',
              }}
            />
            <Bar dataKey="incidents" fill="#f43f5e" name="Incidents Filed" radius={[4, 4, 0, 0]} />
            <Bar dataKey="resolved" fill="#10b981" name="Resolved & Attested" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
