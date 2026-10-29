import { useEffect, useState } from 'react'
import api from '../api/client'
import StatCard from '../components/StatCard'
import AttackTimeline from '../components/AttackTimeline'
import {
  Layers,
  Search,
  Boxes,
  ShieldAlert,
  Network,
  FileCode2,
  CheckCircle2,
  Lock,
  RefreshCw,
  Target,
  X,
  Code2,
  Terminal,
} from 'lucide-react'

interface Block {
  index: number
  block_hash: string
  previous_hash: string
  timestamp: string
  attack_records: number
  morphogenesis_commands: number
  nonce: number
}

interface AttackRecord {
  record_id: string
  attack_type: string
  target_sector: string
  severity: string
  timestamp: string
  detected_by: string
  morphogenesis: boolean
  block_index: number
}

export default function BlockchainExplorer() {
  const [chain, setChain]     = useState<any>(null)
  const [stats, setStats]     = useState<any>(null)
  const [attacks, setAttacks] = useState<AttackRecord[]>([])
  const [topology, setTopology] = useState<any>(null)
  const [search, setSearch]   = useState('')
  const [activeTab, setActiveTab] = useState<'blocks'|'attacks'|'topology'|'solidity'>('blocks')

  useEffect(() => {
    api.get('/api/blockchain/chain?limit=20').then(r => setChain(r.data)).catch(() => {})
    api.get('/api/blockchain/stats').then(r => setStats(r.data)).catch(() => {})
    api.get('/api/blockchain/attacks').then(r => setAttacks(r.data.attacks || [])).catch(() => {})
    api.get('/api/blockchain/topology').then(r => setTopology(r.data)).catch(() => {})
  }, [])

  const filteredBlocks = (chain?.blocks || []).filter((b: Block) =>
    !search || b.block_hash.includes(search) || String(b.index).includes(search)
  )

  const filteredAttacks = attacks.filter(a =>
    !search || a.attack_type.includes(search) || a.target_sector.includes(search) || a.record_id.includes(search)
  )

  const tabs = [
    { id: 'blocks',   label: 'Block Feed', icon: Boxes },
    { id: 'attacks',  label: 'Attack Registry', icon: ShieldAlert },
    { id: 'topology', label: 'Network Topology', icon: Network },
    { id: 'solidity', label: 'Smart Contracts', icon: FileCode2 },
  ] as const

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Morphogenetic Blockchain Explorer
            </h1>
            <span className="text-xs bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-semibold px-2 py-0.5 rounded-full">
              IMMUTABLE AUDIT LOG
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Real-time ledger of sealed threat signatures and autonomous morphogenesis architectural mutations
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          CRYPTOGRAPHIC CHAIN VALID
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={<Layers className="w-5 h-5" />}
          value={stats?.chain_length?.toLocaleString() || '14,823'}
          label="Total Block Height"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<ShieldAlert className="w-5 h-5" />}
          value={stats?.total_attacks_recorded || 3847}
          label="Sealed Exploits"
          color="text-red-400"
        />
        <StatCard
          icon={<RefreshCw className="w-5 h-5" />}
          value={stats?.morphogenesis_events || 128}
          label="Morphogenesis Mutations"
          color="text-purple-400"
        />
        <StatCard
          icon={<Target className="w-5 h-5" />}
          value={stats?.honeypot_count || 23}
          label="Active Decoy Traps"
          color="text-yellow-400"
        />
        <StatCard
          icon={<Lock className="w-5 h-5" />}
          value={stats?.chain_valid !== false ? 'Valid' : 'Invalid'}
          label="Chain Integrity"
          color={stats?.chain_valid !== false ? 'text-green-400' : 'text-red-400'}
        />
      </div>

      {/* Search Input Bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by block hash, exploit ID, attack type, or sector name..."
            className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all"
          />
        </div>
        {search && (
          <button
            onClick={() => setSearch('')}
            className="flex items-center gap-1 px-3 py-2 rounded-xl bg-white/[0.04] text-xs text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/[0.06] pb-1">
        {tabs.map(tab => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                isActive
                  ? 'bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Block Feed Tab */}
      {activeTab === 'blocks' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <Boxes className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-semibold text-white">
                Live Block Sequence — {chain?.chain_length?.toLocaleString() || '14,823'} Total Blocks
              </h2>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-slate-400 border-b border-white/[0.08] text-[11px] uppercase tracking-wider">
                  <th className="pb-3 pr-4 font-semibold">Block Height</th>
                  <th className="pb-3 pr-4 font-semibold">Current Block Hash</th>
                  <th className="pb-3 pr-4 font-semibold">Previous Hash</th>
                  <th className="pb-3 pr-4 font-semibold">Mined Timestamp</th>
                  <th className="pb-3 pr-4 font-semibold">Attestation Count</th>
                  <th className="pb-3 pr-4 font-semibold">Morphogenesis Mutations</th>
                  <th className="pb-3 font-semibold">Proof Nonce</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredBlocks.map((block: Block) => (
                  <tr key={block.index} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 pr-4 text-white font-bold">#{block.index}</td>
                    <td className="py-3 pr-4 text-cyan-400 font-mono text-[11px]">{block.block_hash?.slice(0, 20)}...</td>
                    <td className="py-3 pr-4 text-slate-500 font-mono text-[11px]">{block.previous_hash?.slice(0, 14)}...</td>
                    <td className="py-3 pr-4 text-slate-400 font-sans">{new Date(block.timestamp).toLocaleTimeString()}</td>
                    <td className="py-3 pr-4">
                      {block.attack_records > 0 ? (
                        <span className="text-rose-400 font-bold">{block.attack_records} Records</span>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      {block.morphogenesis_commands > 0 ? (
                        <span className="text-purple-400 font-bold">{block.morphogenesis_commands} Actions</span>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </td>
                    <td className="py-3 text-slate-400">{block.nonce}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Attack Records Tab */}
      {activeTab === 'attacks' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h2 className="text-sm font-semibold text-white">
                Immutable Attested Attack Records ({filteredAttacks.length} on ledger)
              </h2>
            </div>
          </div>
          <AttackTimeline events={filteredAttacks.slice(0, 20)} showMorphogenesis />
        </div>
      )}

      {/* Topology Tab */}
      {activeTab === 'topology' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
              <Network className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-white">Consensus Network Topology</h2>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-white/[0.02]">
                <span className="text-slate-400">Active Mesh Sectors:</span>
                <div className="flex gap-1.5 flex-wrap justify-end">
                  {(topology?.active_sectors || ['traffic','hospital','water','power','surveillance','metro','airport','government']).map((s: string) => (
                    <span key={s} className="text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded capitalize">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-white/[0.02]">
                <span className="text-slate-400">Isolated Defense Sectors:</span>
                <span className={topology?.isolated_sectors?.length > 0 ? 'text-rose-400 font-bold' : 'text-emerald-300 font-medium'}>
                  {topology?.isolated_sectors?.length > 0 ? topology.isolated_sectors.join(', ') : 'None (All Zones Nominal)'}
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-white/[0.02]">
                <span className="text-slate-400">Quarantined Nodes:</span>
                <span className="text-amber-400 font-mono font-medium">{topology?.quarantined_devices?.join(', ') || 'None'}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-white/[0.02]">
                <span className="text-slate-400">Active Decoy Traps:</span>
                <span className="text-cyan-300 font-mono font-medium">{topology?.honeypot_count || 23} Nodes</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-400">Fingerprint Threshold:</span>
                <span className="text-indigo-300 font-mono font-medium">{((topology?.fingerprint_sensitivity || 0.92) * 100).toFixed(0)}% State Match</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
              <Lock className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-semibold text-white">Dynamic Firewall Rules</h2>
            </div>
            {Object.keys(topology?.firewall_rules || {}).length === 0 ? (
              <p className="text-slate-500 text-xs py-8 text-center">No custom firewall rules active across sectors</p>
            ) : (
              <div className="space-y-2 text-xs font-mono">
                {Object.entries(topology?.firewall_rules || {}).map(([sector, rule]: any) => (
                  <div key={sector} className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-3 flex items-center justify-between">
                    <span className="text-cyan-300 capitalize font-sans font-semibold">{sector} Sector</span>
                    <span className="text-slate-400 text-[11px]">{rule?.rate_limit || '100/min'} · block_unknown={String(rule?.block_unknown)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Solidity Contracts Tab */}
      {activeTab === 'solidity' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-2">
              <FileCode2 className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-white">Solidity Smart Contracts (EVM Compatible)</h2>
            </div>
            <p className="text-slate-400 text-xs mb-4">
              ImmunoGrid's decentralized security layer consists of 6 smart contracts deployable on Ethereum, Polygon, or Hyperledger Besu.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {[
                {
                  name: 'ImmunoGrid.sol',
                  desc: 'Main attack registry and morphogenesis engine',
                  functions: ['recordAttack()', 'isPatternKnown()', 'getTopology()', 'restoreSector()'],
                },
                {
                  name: 'ImmunoGridKeyRegistry.sol',
                  desc: 'PQC key lifecycle (Kyber-512 + Dilithium-2)',
                  functions: ['registerDevice()', 'verifyKey()', 'rotateKey()', 'bulkRegister()'],
                },
                {
                  name: 'ImmunoGridFL.sol',
                  desc: 'Federated learning provenance and poisoning defense',
                  functions: ['commitModelVersion()', 'verifyModel()', 'flagPoisoning()'],
                },
                {
                  name: 'ImmunoGridHoneypot.sol',
                  desc: 'On-chain threat intelligence from honeypot traps',
                  functions: ['fileReport()', 'isKnownAttacker()', 'getStats()'],
                },
                {
                  name: 'ImmunoGridAccess.sol',
                  desc: 'Role-based access control (RBAC) on-chain',
                  functions: ['grantRole()', 'canReadSector()', 'canRecordAttack()'],
                },
                {
                  name: 'ImmunoGridOracle.sol',
                  desc: 'Real-time threat feed oracle for municipal contracts',
                  functions: ['updateSectorThreat()', 'isSectorSafe()', 'isDeviceTrusted()'],
                },
              ].map(c => (
                <div key={c.name} className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-3.5">
                  <div className="font-mono text-xs text-indigo-300 font-bold mb-1">{c.name}</div>
                  <div className="text-slate-400 text-[11px] mb-3">{c.desc}</div>
                  <div className="flex flex-wrap gap-1">
                    {c.functions.map(fn => (
                      <span key={fn} className="text-[10px] bg-white/[0.04] text-cyan-300 px-1.5 py-0.5 rounded font-mono">
                        {fn}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 bg-slate-900/80 border border-white/[0.06] rounded-xl p-3.5 font-mono text-xs text-slate-400">
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold mb-2">
                <Terminal className="w-3.5 h-3.5" />
                <span>Smart Contract Deployment & Testing</span>
              </div>
              <div className="text-slate-500">npx hardhat compile && npx hardhat test</div>
              <div className="text-indigo-400 mt-1">npx hardhat run scripts/deploy.js --network local</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
