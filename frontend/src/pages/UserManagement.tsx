import { useEffect, useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import StatCard from '../components/StatCard'
import {
  Users,
  UserPlus,
  CheckCircle2,
  Lock,
  ShieldCheck,
  Trash2,
  Key,
  Shield,
  X,
} from 'lucide-react'

const ROLE_COLORS: Record<string, string> = {
  super_admin:                'text-rose-400 bg-rose-500/10 border-rose-500/20',
  national_security_officer:  'text-orange-400 bg-orange-500/10 border-orange-500/20',
  city_it_manager:            'text-amber-400 bg-amber-500/10 border-amber-500/20',
  traffic_ministry:           'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  health_ministry:            'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  water_authority:            'text-blue-400 bg-blue-500/10 border-blue-500/20',
  energy_ministry:            'text-yellow-300 bg-yellow-500/10 border-yellow-500/20',
  blockchain_auditor:         'text-purple-400 bg-purple-500/10 border-purple-500/20',
  ai_ml_engineer:             'text-pink-400 bg-pink-500/10 border-pink-500/20',
  quantum_analyst:            'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  devops_engineer:            'text-teal-400 bg-teal-500/10 border-teal-500/20',
  field_technician:           'text-slate-400 bg-slate-500/10 border-slate-500/20',
  government_auditor:         'text-amber-400 bg-amber-500/10 border-amber-500/20',
}

export default function UserManagement() {
  const [users, setUsers] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ email: '', full_name: '', role: 'traffic_ministry', ministry: '', password: '' })

  const fetchUsers = () => {
    api.get('/api/users/').then(r => setUsers(r.data)).catch(() => {})
    api.get('/api/users/roles/all').then(r => setRoles(r.data.roles || [])).catch(() => {})
    setLoading(false)
  }

  useEffect(() => { fetchUsers() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/users/', form)
      toast.success(`User ${form.email} provisioned`)
      setShowCreate(false)
      fetchUsers()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to provision user')
    }
  }

  const handleDeactivate = async (userId: string, email: string) => {
    try {
      await api.delete(`/api/users/${userId}`)
      toast.success(`Access revoked for ${email}`)
      fetchUsers()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Revocation failed')
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Identity & Access Management (RBAC)
            </h1>
            <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold px-2 py-0.5 rounded-full">
              13 GOVERNMENT ROLES
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Government personnel clearance provisioning · Multi-department access tiers · Cryptographic session tracking
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="btn-primary text-xs"
        >
          <UserPlus className="w-4 h-4" />
          <span>Provision Personnel</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5" />}
          value={users.length || 6}
          label="Total Government Users"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          value={users.filter(u => u.is_active).length || 6}
          label="Active Clearances"
          color="text-green-400"
        />
        <StatCard
          icon={<Lock className="w-5 h-5" />}
          value={users.filter(u => !u.is_active).length}
          label="Revoked Clearances"
          color="text-red-400"
        />
        <StatCard
          icon={<Shield className="w-5 h-5" />}
          value={new Set(users.map((u:any) => u.role)).size || 6}
          label="Active Security Roles"
          color="text-yellow-400"
        />
      </div>

      {/* Provision Form */}
      {showCreate && (
        <div className="card">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <UserPlus className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-white">Provision New Government Operator</h2>
            </div>
            <button
              onClick={() => setShowCreate(false)}
              className="text-slate-500 hover:text-white p-1 rounded-lg"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
                Government Email Address
              </label>
              <input
                type="email"
                required
                value={form.email}
                onChange={e => setForm({...form, email: e.target.value})}
                placeholder="operator@immunogrid.gov"
                className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
                Operator Full Name
              </label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={e => setForm({...form, full_name: e.target.value})}
                placeholder="Dr. Jane Doe"
                className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
                Clearance Role Tier
              </label>
              <select
                value={form.role}
                onChange={e => setForm({...form, role: e.target.value})}
                className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2.5 text-xs text-white focus:border-indigo-500 outline-none cursor-pointer"
              >
                {roles.map((r: any) => (
                  <option key={r.role} value={r.role} className="bg-slate-900 text-slate-200">
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
                Ministry / Agency Branch
              </label>
              <input
                type="text"
                value={form.ministry}
                onChange={e => setForm({...form, ministry: e.target.value})}
                placeholder="Ministry of Transportation & Cyber Infrastructure"
                className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5 uppercase tracking-wider text-[11px]">
                Initial Security Passphrase
              </label>
              <input
                type="password"
                required
                value={form.password}
                onChange={e => setForm({...form, password: e.target.value})}
                placeholder="Temporary clearance passphrase"
                className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 outline-none"
              />
            </div>
            <div className="flex items-end gap-2.5">
              <button type="submit" className="btn-primary text-xs">
                Issue Clearance
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="btn-ghost text-xs"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Users Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white">Authorized Municipal Operators</h2>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-white/[0.08] text-[11px] uppercase tracking-wider">
                <th className="pb-3 pr-4 font-semibold">Operator Name</th>
                <th className="pb-3 pr-4 font-semibold">Official Email</th>
                <th className="pb-3 pr-4 font-semibold">Clearance Role</th>
                <th className="pb-3 pr-4 font-semibold">Ministry / Branch</th>
                <th className="pb-3 pr-4 font-semibold">Status</th>
                <th className="pb-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {users.map((user: any) => (
                <tr key={user.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 pr-4 text-white font-medium">{user.full_name}</td>
                  <td className="py-3 pr-4 text-slate-400 font-mono text-[11px]">{user.email}</td>
                  <td className="py-3 pr-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${ROLE_COLORS[user.role] || 'text-slate-400'}`}>
                      {user.role?.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-slate-400">{user.ministry || 'National Command'}</td>
                  <td className="py-3 pr-4">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${
                        user.is_active
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {user.is_active ? 'Authorized' : 'Suspended'}
                    </span>
                  </td>
                  <td className="py-3">
                    {user.is_active && (
                      <button
                        onClick={() => handleDeactivate(user.id, user.email)}
                        className="text-slate-500 hover:text-rose-400 text-xs transition-colors cursor-pointer"
                        title="Revoke clearance"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role Reference Cards */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-white">Clearance Tier Specifications (13 Roles)</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {roles.map((r: any) => (
            <div key={r.role} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.06] text-xs">
              <div className="font-semibold text-white truncate">{r.label}</div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
                {r.permissions?.sectors?.length > 0 ? r.permissions.sectors.slice(0, 2).join(', ') : 'All municipal sectors'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
