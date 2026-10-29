import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  LayoutDashboard,
  Atom,
  Brain,
  Layers,
  Target,
  FlaskConical,
  FileText,
  Users,
  Cpu,
  ShieldAlert,
  Terminal,
  ArrowRight,
  Command,
} from 'lucide-react'

interface SearchResult {
  type: 'sector' | 'engine' | 'admin' | 'ops'
  id: string
  label: string
  subtitle: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const SHORTCUTS: SearchResult[] = [
  { type: 'sector', id: 'cc',  label: 'Command Center',    subtitle: 'National smart city security overview', href: '/command-center', icon: LayoutDashboard },
  { type: 'sector', id: 'dev', label: 'IoT Device Registry', subtitle: '500 devices across 8 sectors',        href: '/devices',        icon: Cpu },
  { type: 'sector', id: 'thr', label: 'Threat Intelligence', subtitle: 'Real-time attack vector telemetry',    href: '/threats',        icon: ShieldAlert },
  { type: 'engine', id: 'q',   label: 'Quantum Fingerprint', subtitle: '4-qubit circuit DNA verification',     href: '/quantum',        icon: Atom },
  { type: 'engine', id: 'ai',  label: 'AI Brain (FAC)',      subtitle: 'Federated adversarial consciousness',  href: '/ai-brain',       icon: Brain },
  { type: 'engine', id: 'bc',  label: 'Blockchain Ledger',   subtitle: 'Immutable attack immune memory',       href: '/blockchain',     icon: Layers },
  { type: 'engine', id: 'hp',  label: 'Honeypot Network',    subtitle: 'Autonomous dynamic decoy traps',       href: '/honeypot',       icon: Target },
  { type: 'ops',    id: 'sim', label: 'Simulation Control',  subtitle: 'Virtual attack injection & chaos test',href: '/simulation',     icon: FlaskConical },
  { type: 'admin',  id: 'rpt', label: 'Security Reports',    subtitle: 'Executive intelligence summaries',     href: '/reports',        icon: FileText },
  { type: 'admin',  id: 'usr', label: 'Access Control',      subtitle: 'RBAC user management & permissions',   href: '/users',          icon: Users },
  { type: 'admin',  id: 'devops', label: 'DevOps & Infrastructure', subtitle: 'System health & container ops', href: '/devops',        icon: Terminal },
]

export default function SearchBar() {
  const [query,   setQuery]   = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [open,    setOpen]    = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!query.trim()) {
      setResults(SHORTCUTS.slice(0, 6))
      return
    }

    const q = query.toLowerCase()
    const matched = SHORTCUTS.filter(
      s => s.label.toLowerCase().includes(q) || s.subtitle.toLowerCase().includes(q)
    )
    setResults(matched)
  }, [query])

  const handleSelect = (result: SearchResult) => {
    navigate(result.href)
    setQuery('')
    setOpen(false)
  }

  // Keyboard shortcut: Ctrl+K or Cmd+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen(prev => !prev)
        setTimeout(() => inputRef.current?.focus(), 50)
      }
      if (e.key === 'Escape') {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  return (
    <div className="relative">
      {/* Search trigger button in header */}
      <button
        onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 50) }}
        className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.04] border border-white/[0.08] hover:border-white/20 rounded-xl text-slate-400 text-xs hover:text-slate-200 transition-all w-52 cursor-pointer"
      >
        <Search className="w-3.5 h-3.5 text-slate-500" />
        <span className="truncate">Search system...</span>
        <span className="ml-auto flex items-center gap-0.5 text-[10px] text-slate-400 bg-white/[0.06] border border-white/[0.08] px-1.5 py-0.5 rounded-md font-mono">
          <Command className="w-2.5 h-2.5" />K
        </span>
      </button>

      {/* Command Palette Modal */}
      {open && (
        <>
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 transition-opacity"
            onClick={() => setOpen(false)}
          />
          <div className="fixed top-24 left-1/2 -translate-x-1/2 w-full max-w-lg z-50 px-4">
            <div
              className="rounded-2xl border border-white/[0.12] shadow-2xl overflow-hidden"
              style={{
                background: 'rgba(11, 17, 33, 0.95)',
                backdropFilter: 'blur(24px)',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(99, 102, 241, 0.2)',
              }}
            >
              {/* Input row */}
              <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.08]">
                <Search className="w-4 h-4 text-indigo-400 shrink-0" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Type a command, sector, or security dashboard..."
                  className="flex-1 bg-transparent text-white placeholder-slate-500 outline-none text-sm"
                  autoFocus
                />
                <kbd className="text-[10px] text-slate-400 bg-white/[0.06] border border-white/[0.08] px-2 py-0.5 rounded font-mono">
                  ESC
                </kbd>
              </div>

              {/* Results list */}
              <div className="max-h-72 overflow-y-auto p-1 divide-y divide-white/[0.02]">
                {results.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 text-xs">
                    No results found for "{query}"
                  </div>
                ) : (
                  <div>
                    {!query && (
                      <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Quick System Navigation
                      </div>
                    )}
                    {results.map((result) => {
                      const Icon = result.icon
                      return (
                        <button
                          key={result.id}
                          onClick={() => handleSelect(result)}
                          className="w-full flex items-center gap-3 px-3.5 py-2.5 hover:bg-white/[0.06] rounded-xl transition-colors text-left group cursor-pointer"
                        >
                          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 group-hover:border-indigo-500/40 shrink-0">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-semibold text-white group-hover:text-indigo-200 transition-colors">
                              {result.label}
                            </div>
                            <div className="text-[11px] text-slate-400 truncate mt-0.5">
                              {result.subtitle}
                            </div>
                          </div>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all shrink-0" />
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
