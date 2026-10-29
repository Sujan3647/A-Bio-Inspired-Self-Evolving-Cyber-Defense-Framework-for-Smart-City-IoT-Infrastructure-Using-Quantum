import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import toast from 'react-hot-toast'
import NotificationCenter from './NotificationCenter'
import SearchBar from './SearchBar'
import {
  LayoutDashboard,
  Cpu,
  ShieldAlert,
  FlaskConical,
  Atom,
  Brain,
  Target,
  Layers,
  Search,
  Car,
  Activity,
  Droplets,
  Zap,
  Train,
  Plane,
  FileText,
  FileCheck2,
  Users,
  Terminal,
  LogOut,
  ShieldCheck,
  Radio,
  Lock,
} from 'lucide-react'

interface NavItem {
  to: string
  icon: React.ComponentType<{ className?: string }>
  label: string
  roles: string[]
}

interface NavGroup {
  title: string
  items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Command & Control',
    items: [
      { to: '/command-center', icon: LayoutDashboard, label: 'Command Center', roles: ['super_admin','national_security_officer','city_it_manager'] },
      { to: '/devices',        icon: Cpu,             label: 'IoT Devices',    roles: ['*'] },
      { to: '/threats',        icon: ShieldAlert,     label: 'Threat Intel',   roles: ['*'] },
      { to: '/simulation',     icon: FlaskConical,    label: 'Simulation',     roles: ['super_admin','devops_engineer','city_it_manager','quantum_analyst'] },
    ],
  },
  {
    title: 'Security Engines',
    items: [
      { to: '/quantum',             icon: Atom,   label: 'Quantum Engine', roles: ['super_admin','quantum_analyst','national_security_officer'] },
      { to: '/ai-brain',            icon: Brain,  label: 'AI Brain (FAC)', roles: ['super_admin','ai_ml_engineer','city_it_manager'] },
      { to: '/honeypot',            icon: Target, label: 'Honeypot Decoy', roles: ['super_admin','national_security_officer','city_it_manager','quantum_analyst'] },
      { to: '/blockchain',          icon: Layers, label: 'Immune Ledger',  roles: ['super_admin','national_security_officer','blockchain_auditor','city_it_manager','government_auditor'] },
      { to: '/blockchain/explorer', icon: Search, label: 'Block Explorer', roles: ['super_admin','national_security_officer','blockchain_auditor','city_it_manager','government_auditor'] },
    ],
  },
  {
    title: 'City Sectors',
    items: [
      { to: '/traffic',  icon: Car,      label: 'Traffic Transit', roles: ['super_admin','traffic_ministry','city_it_manager'] },
      { to: '/hospital', icon: Activity, label: 'Healthcare Grid', roles: ['super_admin','health_ministry','city_it_manager'] },
      { to: '/water',    icon: Droplets, label: 'Water Utility',   roles: ['super_admin','water_authority','city_it_manager'] },
      { to: '/power',    icon: Zap,      label: 'Energy & Power',  roles: ['super_admin','energy_ministry','city_it_manager'] },
      { to: '/metro',    icon: Train,    label: 'Metro Rail',      roles: ['super_admin','city_it_manager'] },
      { to: '/airport',  icon: Plane,    label: 'Aviation Hub',    roles: ['super_admin','city_it_manager','national_security_officer'] },
    ],
  },
  {
    title: 'Governance & Ops',
    items: [
      { to: '/reports',    icon: FileText,   label: 'Security Reports', roles: ['super_admin','national_security_officer','government_auditor','city_it_manager'] },
      { to: '/compliance', icon: FileCheck2, label: 'Compliance Audit', roles: ['super_admin','government_auditor','blockchain_auditor'] },
      { to: '/users',      icon: Users,      label: 'Access Control',   roles: ['super_admin','city_it_manager'] },
      { to: '/devops',     icon: Terminal,   label: 'DevOps & Infra',   roles: ['super_admin','devops_engineer'] },
    ],
  },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    toast.success('Logged out from defense session')
    navigate('/login')
  }

  // Find active navigation item
  const allItems = NAV_GROUPS.flatMap(g => g.items)
  const activeItem = allItems.find(i => location.pathname === i.to || location.pathname.startsWith(`${i.to}/`))
  const ActiveIcon = activeItem?.icon || LayoutDashboard

  return (
    <div
      className="flex h-screen overflow-hidden text-slate-100"
      style={{
        background: 'radial-gradient(circle at 50% 0%, #0d1527 0%, #060913 60%, #03050a 100%)',
      }}
    >
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside
        className="w-64 flex flex-col shrink-0 border-r border-white/[0.07] z-20"
        style={{ background: 'rgba(8, 12, 22, 0.95)', backdropFilter: 'blur(20px)' }}
      >
        {/* Brand Logo Header */}
        <div className="px-5 py-4 border-b border-white/[0.07]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 shrink-0 glow-indigo">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="font-bold text-white text-sm tracking-tight flex items-center gap-1.5">
                Immuno<span className="text-indigo-400">Grid</span>
                <span className="text-[10px] bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold px-1.5 py-0.2 rounded">
                  v1.4
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-medium tracking-wide uppercase truncate mt-0.5">
                Defense Command
              </div>
            </div>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5">
          {NAV_GROUPS.map((group) => {
            const visible = group.items.filter(
              item => item.roles.includes('*') || item.roles.includes(user?.role || '')
            )
            if (visible.length === 0) return null
            return (
              <div key={group.title}>
                <div className="section-title">{group.title}</div>
                <div className="space-y-0.5">
                  {visible.map((item) => {
                    const Icon = item.icon
                    return (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                          `flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 group ${
                            isActive
                              ? 'nav-active'
                              : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
                          }`
                        }
                      >
                        <Icon className="w-4 h-4 shrink-0 transition-transform duration-150 group-hover:scale-110" />
                        <span className="truncate">{item.label}</span>
                      </NavLink>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </nav>

        {/* User Identity Footer */}
        <div className="p-3 border-t border-white/[0.07]">
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-indigo-200 shrink-0 bg-indigo-600/30 border border-indigo-500/40">
              {user?.full_name?.charAt(0) || 'O'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-slate-200 truncate">{user?.full_name || 'Active Operator'}</div>
              <div className="text-[10px] text-indigo-400 capitalize truncate mt-0.5">
                {user?.role?.replace(/_/g, ' ') || 'Authorized User'}
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out Session"
              className="text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 p-1.5 rounded-lg transition-colors shrink-0 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Workspace ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header
          className="h-14 flex items-center justify-between px-6 shrink-0 border-b border-white/[0.07] z-10"
          style={{ background: 'rgba(9, 14, 25, 0.85)', backdropFilter: 'blur(16px)' }}
        >
          {/* Breadcrumb / Title */}
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <ActiveIcon className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 font-medium">ImmunoGrid</span>
              <span className="text-slate-600">/</span>
              <h1 className="text-sm font-semibold text-white">
                {activeItem?.label || 'Security Operations'}
              </h1>
            </div>
          </div>

          {/* Right Header Status Bar */}
          <div className="flex items-center gap-3">
            {/* Global Search Component */}
            <SearchBar />

            {/* PQC Security Engine Status */}
            <div className="hidden lg:flex items-center gap-1.5 text-[11px] font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/25 px-2.5 py-1 rounded-full">
              <Lock className="w-3 h-3 text-indigo-400" />
              <span>PQC KYBER-512</span>
            </div>

            {/* Live Defense Indicator */}
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-300 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              <span>DEFENSE ARMED</span>
            </div>

            {/* Notifications Dropdown */}
            <NotificationCenter />
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
