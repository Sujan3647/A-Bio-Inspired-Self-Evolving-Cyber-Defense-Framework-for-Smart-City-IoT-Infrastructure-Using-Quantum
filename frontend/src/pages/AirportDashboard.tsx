import { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import {
  Plane,
  Cpu,
  CheckCircle2,
  Search,
  Users,
  AlertTriangle,
  Building2,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react'

export default function AirportDashboard() {
  const stats = {
    total_devices: 30,
    online: 29,
    scanners_active: 18,
    passengers_scanned_today: 12450,
    security_alerts: 1,
    false_alarm_rate: '0.3%',
  }

  const zones = [
    { name: 'Terminal 1 - International', devices: 8, status: 'normal', throughput: 3200 },
    { name: 'Terminal 2 - Domestic',      devices: 6, status: 'normal', throughput: 2800 },
    { name: 'Immigration & Biometrics',   devices: 5, status: 'alert',  throughput: 1200 },
    { name: 'Customs & Border Control',  devices: 4, status: 'normal', throughput: 980 },
    { name: 'Runway North Airfield Radar', devices: 4, status: 'normal', throughput: 0 },
    { name: 'Air Cargo Logistics Bay',    devices: 3, status: 'normal', throughput: 450 },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              International Airport Aviation Cyber Defense
            </h1>
            <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold px-2 py-0.5 rounded-full">
              CIVIL AVIATION CYBERSECURITY
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            Biometric gate security · Runway perimeter radar telemetry · Quantum-authenticated scanner communications
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          AIRSPACE PERIMETER SECURE
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Cpu className="w-5 h-5" />}
          value={stats.total_devices}
          label="Aviation IoT Nodes"
          color="text-cyan-400"
          pulse
        />
        <StatCard
          icon={<Search className="w-5 h-5" />}
          value={stats.scanners_active}
          label="Active Biometric Scanners"
          color="text-green-400"
          trend="100% Calibrated"
        />
        <StatCard
          icon={<Users className="w-5 h-5" />}
          value={stats.passengers_scanned_today.toLocaleString()}
          label="Passengers Screened"
          color="text-yellow-400"
          sub="No unauthorized bypass"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          value={stats.security_alerts}
          label="Border Security Alerts"
          color="text-orange-400"
          sub="Immigration gate held"
        />
      </div>

      {/* Zone Status */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/[0.06]">
          <Building2 className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Terminal & Runway Operational Zones</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {zones.map((zone) => (
            <div
              key={zone.name}
              className={`p-3.5 rounded-xl border transition-all ${
                zone.status === 'alert'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-white/[0.02] border-white/[0.06]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-white truncate">{zone.name}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    zone.status === 'alert'
                      ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                      : 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  }`}
                />
              </div>
              <div className="text-[11px] text-slate-400 font-mono">{zone.devices} Connected Nodes</div>
              {zone.throughput > 0 && (
                <div className="text-[11px] text-cyan-300 font-mono mt-1">
                  {zone.throughput.toLocaleString()} passengers / day
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Scanner Performance & Perimeter Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <Search className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Biometric Scanner Performance</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Mean Screening Latency:</span>
              <span className="text-cyan-300 font-mono font-medium">18.4 sec / passenger</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">False Positive Alarm Rate:</span>
              <span className="text-emerald-400 font-mono font-medium">{stats.false_alarm_rate}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Biometric Template Integrity:</span>
              <span className="text-emerald-400 font-semibold">100% Kyber-512 Encrypted</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/[0.06]">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Runway ADS-B & Perimeter Defense</h2>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">ADS-B Signal Spoofing Protection:</span>
              <span className="text-emerald-400 font-semibold">Active — 4-Qubit QBF</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.02]">
              <span className="text-slate-400">Perimeter Intrusion Sensors:</span>
              <span className="text-emerald-400 font-medium">All 4 Radar Units Online</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Air Traffic Control Link:</span>
              <span className="text-cyan-300 font-mono font-medium">Post-Quantum Dilithium Signed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
