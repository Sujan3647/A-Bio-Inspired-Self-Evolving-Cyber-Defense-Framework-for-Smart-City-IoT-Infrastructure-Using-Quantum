import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import LoginPage from './pages/Login'
import Layout from './components/Layout'
import CommandCenter from './pages/CommandCenter'
import TrafficDashboard from './pages/TrafficDashboard'
import HospitalDashboard from './pages/HospitalDashboard'
import WaterDashboard from './pages/WaterDashboard'
import PowerDashboard from './pages/PowerDashboard'
import MetroDashboard from './pages/MetroDashboard'
import AirportDashboard from './pages/AirportDashboard'
import BlockchainLedger from './pages/BlockchainLedger'
import BlockchainExplorer from './pages/BlockchainExplorer'
import AIBrainDashboard from './pages/AIBrainDashboard'
import QuantumDashboard from './pages/QuantumDashboard'
import DevicesDashboard from './pages/DevicesDashboard'
import ThreatsDashboard from './pages/ThreatsDashboard'
import HoneypotDashboard from './pages/HoneypotDashboard'
import ComplianceDashboard from './pages/ComplianceDashboard'
import DevOpsDashboard from './pages/DevOpsDashboard'
import SimulationControl from './pages/SimulationControl'
import UserManagement from './pages/UserManagement'
import ReportsDashboard from './pages/ReportsDashboard'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/command-center" replace />} />
        {/* Command & Control */}
        <Route path="command-center"  element={<CommandCenter />} />
        <Route path="devices"         element={<DevicesDashboard />} />
        <Route path="threats"         element={<ThreatsDashboard />} />
        <Route path="simulation"      element={<SimulationControl />} />
        {/* Security Engines */}
        <Route path="quantum"         element={<QuantumDashboard />} />
        <Route path="ai-brain"        element={<AIBrainDashboard />} />
        <Route path="honeypot"        element={<HoneypotDashboard />} />
        <Route path="blockchain"      element={<BlockchainLedger />} />
        <Route path="blockchain/explorer" element={<BlockchainExplorer />} />
        {/* City Sectors */}
        <Route path="traffic"         element={<TrafficDashboard />} />
        <Route path="hospital"        element={<HospitalDashboard />} />
        <Route path="water"           element={<WaterDashboard />} />
        <Route path="power"           element={<PowerDashboard />} />
        <Route path="metro"           element={<MetroDashboard />} />
        <Route path="airport"         element={<AirportDashboard />} />
        {/* Administration */}
        <Route path="reports"         element={<ReportsDashboard />} />
        <Route path="compliance"      element={<ComplianceDashboard />} />
        <Route path="users"           element={<UserManagement />} />
        <Route path="devops"          element={<DevOpsDashboard />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
