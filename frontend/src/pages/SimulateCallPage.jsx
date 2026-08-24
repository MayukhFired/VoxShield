import React, { useState, useRef, useEffect } from 'react'
import { Phone, PhoneOff, AlertTriangle, Shield, User, Clock, CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'

// Demo scenarios
const SCENARIOS = [
  {
    id: 'scam_call',
    name: 'Scam Call (Cloned Voice)',
    description: 'Unknown number calls with a cloned voice. System should detect it.',
    callerName: 'Unknown Number',
    callerNumber: '+91 87654 32100',
    isBlacklisted: false,
    expectedVerdict: 'fake',
  },
  {
    id: 'real_call',
    name: 'Legitimate Call',
    description: 'A real person calls. System should confirm authenticity.',
    callerName: 'Mom',
    callerNumber: '+91 98765 43210',
    isBlacklisted: false,
    expectedVerdict: 'real',
  },
  {
    id: 'known_scammer',
    name: 'Known Scammer',
    description: 'A previously blacklisted number calls. Pre-call alert triggers.',
    callerName: 'Unknown Number',
    callerNumber: '+91 11111 22222',
    isBlacklisted: true,
    blacklistReports: 7,
    expectedVerdict: 'fake',
  },
]

export default function SimulateCallPage() {
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [callState, setCallState] = useState('idle') // idle | ringing | blacklist_warning | active | detecting | result | ended
  const [detectionResult, setDetectionResult] = useState(null)
  const [timer, setTimer] = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const startScenario = (scenario) => {
    setSelectedScenario(scenario)
    setCallState('ringing')
    setDetectionResult(null)
    setTimer(0)
  }

  const answerCall = () => {
    if (selectedScenario.isBlacklisted) {
      setCallState('blacklist_warning')
    } else {
      startCall()
    }
  }

  const proceedDespiteWarning = () => {
    startCall()
  }

  const startCall = () => {
    setCallState('active')
    
    // Start timer
    timerRef.current = setInterval(() => {
      setTimer(t => t + 1)
    }, 1000)
    
    // Simulate detection after 3 seconds
    setTimeout(() => {
      setCallState('detecting')
    }, 3000)
    
    // Show result after 5 seconds
    setTimeout(() => {
      setCallState('result')
      setDetectionResult({
        verdict: selectedScenario.expectedVerdict,
        confidence: selectedScenario.expectedVerdict === 'fake' ? 0.94 : 0.89,
      })
    }, 5000)
  }

  const endCall = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    setCallState('ended')
  }

  const reportAndEnd = async () => {
    // Report the number
    try {
      await axios.post('/api/blacklist/report', {
        phone_number: selectedScenario.callerNumber,
        confidence_score: detectionResult?.confidence || 0.9,
        notes: 'Reported via call simulation',
      })
    } catch (err) {
      console.error('Report failed:', err)
    }
    endCall()
  }

  const resetSimulation = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    setSelectedScenario(null)
    setCallState('idle')
    setDetectionResult(null)
    setTimer(0)
  }

  const formatTime = (s) => {
    const mins = Math.floor(s / 60)
    const secs = s % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Scenario selection screen
  if (callState === 'idle') {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Call Simulation</h1>
          <p className="text-gray-400">Experience how VoiceShield protects you during phone calls.</p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-4">
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => startScenario(scenario)}
              className="card text-left hover:border-primary-500/50 transition-all duration-200 group"
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${
                scenario.expectedVerdict === 'fake' ? 'bg-red-500/10' : 'bg-green-500/10'
              }`}>
                <Phone className={`w-5 h-5 ${scenario.expectedVerdict === 'fake' ? 'text-danger' : 'text-safe'}`} />
              </div>
              <h3 className="font-semibold mb-1 group-hover:text-primary-400 transition-colors">{scenario.name}</h3>
              <p className="text-gray-400 text-sm">{scenario.description}</p>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Call simulation UI
  return (
    <div className="max-w-md mx-auto px-4 py-12">
      <div className="bg-dark-800 rounded-3xl overflow-hidden border border-dark-700 shadow-2xl">
        {/* Call Header */}
        <div className="bg-gradient-to-b from-dark-700 to-dark-800 p-8 text-center">
          <div className="w-20 h-20 bg-dark-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <User className="w-10 h-10 text-gray-400" />
          </div>
          <p className="text-xl font-semibold">{selectedScenario.callerName}</p>
          <p className="text-gray-400 text-sm">{selectedScenario.callerNumber}</p>
          
          {callState === 'ringing' && (
            <p className="text-primary-400 mt-2 animate-pulse">Incoming call...</p>
          )}
          {(callState === 'active' || callState === 'detecting' || callState === 'result') && (
            <div className="flex items-center justify-center gap-2 mt-2 text-gray-400">
              <Clock className="w-4 h-4" />
              <span>{formatTime(timer)}</span>
            </div>
          )}
        </div>

        {/* Blacklist Warning */}
        {callState === 'blacklist_warning' && (
          <div className="p-6 bg-red-500/10 border-t border-b border-red-500/30">
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle className="w-8 h-8 text-danger" />
              <div>
                <p className="font-bold text-danger">SCAM ALERT</p>
                <p className="text-sm text-gray-400">This number has been reported by {selectedScenario.blacklistReports} users</p>
              </div>
            </div>
            <p className="text-gray-300 text-sm mb-4">
              This number is in our community blacklist as a confirmed scam number. 
              We strongly recommend not answering this call.
            </p>
            <div className="flex gap-3">
              <button onClick={resetSimulation} className="flex-1 bg-dark-700 py-2 rounded-lg text-sm font-medium hover:bg-dark-600 transition-colors">
                Decline
              </button>
              <button onClick={proceedDespiteWarning} className="flex-1 bg-red-500/20 border border-red-500/30 py-2 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/30 transition-colors">
                Answer Anyway
              </button>
            </div>
          </div>
        )}

        {/* Detection Status */}
        {callState === 'detecting' && (
          <div className="p-6 bg-primary-500/5 border-t border-primary-500/30">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center animate-pulse">
                <Shield className="w-4 h-4 text-primary-400" />
              </div>
              <div>
                <p className="font-medium text-primary-400">Analyzing voice...</p>
                <p className="text-sm text-gray-400">AI is checking voice authenticity</p>
              </div>
            </div>
          </div>
        )}

        {/* Detection Result */}
        {callState === 'result' && detectionResult && (
          <div className={`p-6 border-t ${
            detectionResult.verdict === 'fake' 
              ? 'bg-red-500/10 border-red-500/30' 
              : 'bg-green-500/10 border-green-500/30'
          }`}>
            <div className="flex items-center gap-3 mb-3">
              {detectionResult.verdict === 'fake' ? (
                <XCircle className="w-8 h-8 text-danger" />
              ) : (
                <CheckCircle className="w-8 h-8 text-safe" />
              )}
              <div>
                <p className={`font-bold ${detectionResult.verdict === 'fake' ? 'text-danger' : 'text-safe'}`}>
                  {detectionResult.verdict === 'fake' ? 'SYNTHETIC VOICE DETECTED' : 'VOICE VERIFIED — REAL'}
                </p>
                <p className="text-sm text-gray-400">
                  Confidence: {(detectionResult.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            {detectionResult.verdict === 'fake' && (
              <p className="text-sm text-gray-300">
                This voice shows signs of AI generation. This may be an impersonation attack.
              </p>
            )}
          </div>
        )}

        {/* Call Actions */}
        <div className="p-6 flex justify-center gap-4">
          {callState === 'ringing' && (
            <>
              <button onClick={resetSimulation} className="w-14 h-14 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors">
                <PhoneOff className="w-6 h-6 text-white" />
              </button>
              <button onClick={answerCall} className="w-14 h-14 rounded-full bg-green-500 flex items-center justify-center hover:bg-green-600 transition-colors">
                <Phone className="w-6 h-6 text-white" />
              </button>
            </>
          )}
          
          {(callState === 'active' || callState === 'detecting') && (
            <button onClick={endCall} className="w-14 h-14 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors">
              <PhoneOff className="w-6 h-6 text-white" />
            </button>
          )}
          
          {callState === 'result' && (
            <div className="flex gap-3 w-full">
              <button onClick={endCall} className="flex-1 bg-dark-700 py-3 rounded-lg font-medium hover:bg-dark-600 transition-colors">
                End Call
              </button>
              {detectionResult?.verdict === 'fake' && (
                <button onClick={reportAndEnd} className="flex-1 btn-danger py-3 flex items-center justify-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> Report & End
                </button>
              )}
            </div>
          )}
          
          {callState === 'ended' && (
            <button onClick={resetSimulation} className="btn-primary">
              Try Another Scenario
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
