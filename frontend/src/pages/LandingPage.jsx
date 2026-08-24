import React from 'react'
import { Link } from 'react-router-dom'
import { Shield, Upload, Mic, AlertTriangle, Phone, ArrowRight, Activity } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 px-4 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-900/20 to-transparent pointer-events-none" />
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <div className="flex justify-center mb-6">
            <div className="bg-primary-500/10 p-4 rounded-2xl border border-primary-500/20 animate-glow">
              <Shield className="w-16 h-16 text-primary-400" />
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Your AI Shield Against <br />Voice Cloning Attacks
          </h1>
          <p className="text-xl text-gray-400 mb-4 max-w-2xl mx-auto">
            Detect synthetic and cloned voices in real-time using advanced AI. 
            Protect yourself and your community from voice impersonation fraud.
          </p>
          <p className="text-danger font-semibold mb-8">
            70% of people cannot distinguish cloned voices from real ones during live calls.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/detect" className="btn-primary flex items-center justify-center gap-2 text-lg">
              Try It Now <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/simulate" className="bg-dark-700 hover:bg-dark-600 text-white font-medium px-6 py-3 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 text-lg border border-dark-600">
              Watch Demo <Phone className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 px-4 border-y border-dark-700 bg-dark-800/50">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-3xl font-bold text-primary-400">3 sec</div>
            <div className="text-gray-500 text-sm mt-1">to clone a voice</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-danger">70%</div>
            <div className="text-gray-500 text-sm mt-1">can't detect fakes</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-safe">99.2%</div>
            <div className="text-gray-500 text-sm mt-1">our detection accuracy</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-warning">&lt;2s</div>
            <div className="text-gray-500 text-sm mt-1">analysis time</div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card text-center">
              <div className="bg-primary-500/10 w-14 h-14 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Mic className="w-7 h-7 text-primary-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2">1. Listen</h3>
              <p className="text-gray-400">Upload audio or activate live mic. The system captures the voice signal for analysis.</p>
            </div>
            <div className="card text-center">
              <div className="bg-primary-500/10 w-14 h-14 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Activity className="w-7 h-7 text-primary-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2">2. Analyze</h3>
              <p className="text-gray-400">AI examines acoustic features invisible to human ears — pitch patterns, breath markers, spectral signatures.</p>
            </div>
            <div className="card text-center">
              <div className="bg-primary-500/10 w-14 h-14 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Shield className="w-7 h-7 text-primary-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2">3. Protect</h3>
              <p className="text-gray-400">Get instant verdict with confidence score. Report scam numbers to protect the community.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 bg-dark-800/30">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="card flex gap-4">
              <Upload className="w-8 h-8 text-primary-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-1">Upload & Detect</h3>
                <p className="text-gray-400">Upload any voice recording — WAV, MP3, FLAC. Get instant analysis with visual spectrogram breakdown.</p>
              </div>
            </div>
            <div className="card flex gap-4">
              <Mic className="w-8 h-8 text-primary-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-1">Real-Time Mic Analysis</h3>
                <p className="text-gray-400">Stream audio from your microphone for live detection with real-time confidence meter.</p>
              </div>
            </div>
            <div className="card flex gap-4">
              <AlertTriangle className="w-8 h-8 text-warning flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-1">Community Blacklist</h3>
                <p className="text-gray-400">Report scam numbers. When one user catches a scammer, everyone else is protected.</p>
              </div>
            </div>
            <div className="card flex gap-4">
              <Phone className="w-8 h-8 text-safe flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-1">Call Simulation</h3>
                <p className="text-gray-400">See how the system works during real phone calls with our interactive demo.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Privacy Section */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-6">Privacy First</h2>
          <p className="text-gray-400 mb-8">Your voice data never leaves your control.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['Zero Audio Storage', 'On-Device Processing', 'No Transcription', 'No Cloud Upload'].map((item) => (
              <div key={item} className="bg-dark-800 border border-dark-700 rounded-lg p-4">
                <p className="text-sm text-gray-300">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-dark-700 text-center text-gray-500 text-sm">
        VoiceShield — AI-Powered Voice Cloning Detection | Smart India Hackathon 2025
      </footer>
    </div>
  )
}
