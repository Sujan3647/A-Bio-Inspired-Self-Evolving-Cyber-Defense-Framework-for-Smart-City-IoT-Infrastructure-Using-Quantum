import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useAuthStore } from '../store/auth'
import { ShieldCheck, Eye, EyeOff, Lock, Mail, KeyRound, Sparkles, CheckCircle2 } from 'lucide-react'

const DEMO_ACCOUNTS = [
  { email: 'admin@immunogrid.gov',    password: 'Admin@123',    role: 'Super Admin', tag: 'Full Clearance' },
  { email: 'security@immunogrid.gov', password: 'Security@123', role: 'Security Officer', tag: 'Threat Intel' },
  { email: 'traffic@immunogrid.gov',  password: 'Traffic@123',  role: 'Traffic Ministry', tag: 'Transit Sector' },
  { email: 'hospital@immunogrid.gov', password: 'Health@123',   role: 'Health Ministry', tag: 'Medical Sector' },
  { email: 'quantum@immunogrid.gov',  password: 'Quantum@123',  role: 'Quantum Analyst', tag: 'PQC Engine' },
  { email: 'auditor@immunogrid.gov',  password: 'Audit@123',    role: 'Govt Auditor', tag: 'Ledger Audit' },
]

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/login', { email, password })
      const me = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      })
      login(data.access_token, me.data)
      toast.success(`Authenticated: Welcome, ${me.data.full_name}`)
      navigate('/command-center')
    } catch {
      toast.error('Authentication failed. Check credentials or use a demo profile.')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (acc: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(acc.email)
    setPassword(acc.password)
    toast.success(`Loaded profile: ${acc.role}`)
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at 50% 20%, #111a36 0%, #070b14 70%, #03050a 100%)',
      }}
    >
      {/* Background ambient glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-600/15 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-80 h-80 bg-cyan-600/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/25 shadow-lg shadow-indigo-500/20 mb-4 glow-indigo">
            <ShieldCheck className="w-10 h-10 text-indigo-400" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center justify-center gap-2">
            Immuno<span className="text-indigo-400">Grid</span>
          </h1>
          <p className="text-slate-400 mt-2 text-xs font-medium tracking-wide uppercase">
            Bio-Inspired Smart City Cyber Defense Command
          </p>
        </div>

        {/* Login Card */}
        <div
          className="rounded-2xl p-7 border border-white/10 backdrop-blur-2xl"
          style={{
            background: 'rgba(13, 21, 39, 0.85)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(99, 102, 241, 0.15)',
          }}
        >
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/[0.08]">
            <div>
              <h2 className="text-base font-semibold text-white">Operator Sign In</h2>
              <p className="text-xs text-slate-400 mt-0.5">Enter high-assurance defense credentials</p>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              PORTAL ARMED
            </span>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Email Field */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Operator ID / Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@immunogrid.gov"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Passphrase / Token
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter security passphrase"
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors p-1"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me + Help */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500/50 cursor-pointer"
                />
                <span className="text-xs text-slate-400">Remember credentials</span>
              </label>
              <button
                type="button"
                className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                onClick={() => toast('Demo mode active: Select a pre-configured clearance profile below.')}
              >
                Passphrase help?
              </button>
            </div>

            {/* Login Button */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 mt-2 rounded-xl text-white font-semibold text-sm transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/30 active:scale-[0.98] disabled:opacity-50 cursor-pointer"
              style={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #7c3aed 100%)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Verifying Quantum Identity...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <KeyRound className="w-4 h-4" />
                  Authenticate to Command Center
                </span>
              )}
            </button>
          </form>
        </div>

        {/* Demo Accounts */}
        <div className="mt-6">
          <div className="flex items-center justify-center gap-2 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <p className="text-xs text-slate-400 font-medium tracking-wide uppercase">
              Pre-Configured Clearance Profiles
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                onClick={() => fillDemo(acc)}
                className="group relative text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/[0.06] hover:border-indigo-500/40 transition-all duration-150 cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors">
                    {acc.role}
                  </span>
                  <span className="text-[10px] text-slate-500 group-hover:text-slate-400 transition-colors">
                    {acc.tag}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 truncate mt-0.5">
                  {acc.email}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
