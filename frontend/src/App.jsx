import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { Shield, Upload, Mic, Phone, AlertTriangle } from 'lucide-react'
import LandingPage from './pages/LandingPage'
import DetectPage from './pages/DetectPage'
import LiveMicPage from './pages/LiveMicPage'
import BlacklistPage from './pages/BlacklistPage'
import SimulateCallPage from './pages/SimulateCallPage'

function Navbar() {
  const linkClass = ({ isActive }) =>
    `flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${
      isActive
        ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
        : 'text-gray-400 hover:text-white hover:bg-dark-700'
    }`

  return (
    <nav className="bg-dark-800 border-b border-dark-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <NavLink to="/" className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-primary-500" />
            <span className="text-xl font-bold">VoiceShield</span>
          </NavLink>
          <div className="flex items-center gap-2">
            <NavLink to="/detect" className={linkClass}>
              <Upload className="w-4 h-4" />
              <span className="hidden sm:inline">Detect</span>
            </NavLink>
            <NavLink to="/live" className={linkClass}>
              <Mic className="w-4 h-4" />
              <span className="hidden sm:inline">Live Mic</span>
            </NavLink>
            <NavLink to="/blacklist" className={linkClass}>
              <AlertTriangle className="w-4 h-4" />
              <span className="hidden sm:inline">Blacklist</span>
            </NavLink>
            <NavLink to="/simulate" className={linkClass}>
              <Phone className="w-4 h-4" />
              <span className="hidden sm:inline">Simulate</span>
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-dark-900">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/detect" element={<DetectPage />} />
            <Route path="/live" element={<LiveMicPage />} />
            <Route path="/blacklist" element={<BlacklistPage />} />
            <Route path="/simulate" element={<SimulateCallPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}
