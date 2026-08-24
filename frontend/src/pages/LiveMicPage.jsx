import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Mic, MicOff, Activity, Shield } from 'lucide-react'

export default function LiveMicPage() {
  const [isListening, setIsListening] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [audioLevel, setAudioLevel] = useState(0)
  
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const animationRef = useRef(null)
  const streamRef = useRef(null)

  const startListening = async () => {
    try {
      setError(null)
      setResult(null)
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { sampleRate: 16000, channelCount: 1 } 
      })
      streamRef.current = stream
      
      // Set up audio analyzer for visual level meter
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      source.connect(analyserRef.current)
      
      // Start level monitoring
      monitorAudioLevel()
      
      // Connect WebSocket
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws/stream`
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        // Start recording in 3-second chunks
        startRecording(stream)
      }
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.error) {
          setError(data.error)
        } else {
          setResult(data)
        }
      }
      
      wsRef.current.onerror = () => {
        setError('WebSocket connection failed. Make sure the backend is running.')
      }
      
      wsRef.current.onclose = () => {
        console.log('WebSocket closed')
      }
      
      setIsListening(true)
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Microphone permission denied. Please allow microphone access.')
      } else {
        setError(`Failed to start: ${err.message}`)
      }
    }
  }

  const startRecording = (stream) => {
    const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    mediaRecorderRef.current = mediaRecorder
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
        event.data.arrayBuffer().then((buffer) => {
          wsRef.current.send(buffer)
        })
      }
    }
    
    // Record in 3-second chunks
    mediaRecorder.start(3000)
  }

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    
    const update = () => {
      analyserRef.current.getByteFrequencyData(dataArray)
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length
      setAudioLevel(average / 255)
      animationRef.current = requestAnimationFrame(update)
    }
    
    update()
  }

  const stopListening = () => {
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    
    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    // Stop audio stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    
    // Stop audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
    
    // Cancel animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
    }
    
    setIsListening(false)
    setAudioLevel(0)
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening()
    }
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Live Microphone Detection</h1>
        <p className="text-gray-400">Stream audio from your microphone for real-time voice authenticity analysis.</p>
      </div>

      {/* Mic Control */}
      <div className="card text-center py-12">
        <div className="relative inline-block">
          {/* Glow ring */}
          {isListening && (
            <div 
              className="absolute inset-0 rounded-full transition-all duration-150"
              style={{
                transform: `scale(${1 + audioLevel * 0.5})`,
                background: `radial-gradient(circle, rgba(59, 130, 246, ${audioLevel * 0.3}) 0%, transparent 70%)`,
              }}
            />
          )}
          <button
            onClick={isListening ? stopListening : startListening}
            className={`relative w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${
              isListening 
                ? 'bg-red-500/20 border-2 border-red-500 hover:bg-red-500/30' 
                : 'bg-primary-500/20 border-2 border-primary-500 hover:bg-primary-500/30'
            }`}
          >
            {isListening ? (
              <MicOff className="w-12 h-12 text-red-400" />
            ) : (
              <Mic className="w-12 h-12 text-primary-400" />
            )}
          </button>
        </div>
        
        <p className="mt-6 text-gray-400">
          {isListening ? 'Listening... Click to stop' : 'Click to start live detection'}
        </p>
        
        {/* Audio Level Bar */}
        {isListening && (
          <div className="mt-6 max-w-xs mx-auto">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary-400" />
              <div className="flex-1 h-2 bg-dark-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary-500 rounded-full transition-all duration-100"
                  style={{ width: `${audioLevel * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Live Result */}
      {result && (
        <div className={`mt-6 card border-2 ${
          result.verdict === 'real'
            ? 'border-green-500/30 bg-green-500/5'
            : 'border-red-500/30 bg-red-500/5'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className={`w-8 h-8 ${result.verdict === 'real' ? 'text-safe' : 'text-danger'}`} />
              <div>
                <p className={`text-2xl font-bold ${result.verdict === 'real' ? 'text-safe' : 'text-danger'}`}>
                  {result.verdict === 'real' ? 'REAL' : 'FAKE'}
                </p>
                <p className="text-gray-400 text-sm">Last analysis result</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{(result.confidence * 100).toFixed(0)}%</p>
              <p className="text-gray-500 text-sm">confidence</p>
            </div>
          </div>
          
          {/* Quick check summary */}
          {result.signal_summary && (
            <div className="mt-4 pt-4 border-t border-dark-700 flex gap-4 text-sm">
              <span className="text-safe">{result.signal_summary.checks_passed} checks passed</span>
              <span className="text-danger">{result.signal_summary.checks_failed} checks failed</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
