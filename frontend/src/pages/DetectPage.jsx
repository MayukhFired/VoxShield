import React, { useState, useCallback } from 'react'
import { Upload, FileAudio, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react'
import axios from 'axios'
import Spectrogram from '../components/Spectrogram'

export default function DetectPage() {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) {
      setFile(dropped)
      setResult(null)
      setError(null)
    }
  }, [])

  const handleFileSelect = (e) => {
    const selected = e.target.files[0]
    if (selected) {
      setFile(selected)
      setResult(null)
      setError(null)
    }
  }

  const analyzeFile = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/detect', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Voice Authenticity Detection</h1>
        <p className="text-gray-400">Upload an audio file to analyze if the voice is real or AI-generated.</p>
      </div>

      {/* Upload Zone */}
      <div
        className={`card border-2 border-dashed transition-all duration-200 cursor-pointer ${
          isDragging ? 'border-primary-500 bg-primary-500/5' : 'border-dark-600 hover:border-primary-500/50'
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={handleFileSelect}
        />
        <div className="text-center py-8">
          {file ? (
            <div className="flex flex-col items-center gap-3">
              <FileAudio className="w-12 h-12 text-primary-400" />
              <p className="text-lg font-medium">{file.name}</p>
              <p className="text-gray-500 text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className="w-12 h-12 text-gray-500" />
              <p className="text-lg text-gray-400">Drag & drop an audio file here</p>
              <p className="text-sm text-gray-500">or click to browse — WAV, MP3, FLAC, OGG (max 10MB)</p>
            </div>
          )}
        </div>
      </div>

      {/* Analyze Button */}
      {file && (
        <div className="text-center mt-6">
          <button
            onClick={analyzeFile}
            disabled={loading}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                Analyze Voice
              </>
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Verdict Banner */}
          <div className={`card text-center py-8 border-2 ${
            result.verdict === 'real'
              ? 'border-green-500/30 bg-green-500/5'
              : 'border-red-500/30 bg-red-500/5'
          }`}>
            {result.verdict === 'real' ? (
              <CheckCircle className="w-16 h-16 text-safe mx-auto mb-3" />
            ) : (
              <XCircle className="w-16 h-16 text-danger mx-auto mb-3" />
            )}
            <h2 className={`text-4xl font-bold mb-2 ${
              result.verdict === 'real' ? 'text-safe' : 'text-danger'
            }`}>
              {result.verdict === 'real' ? 'REAL VOICE' : 'SYNTHETIC VOICE DETECTED'}
            </h2>
            <p className="text-gray-400 text-lg">
              Confidence: <span className="font-semibold text-white">{(result.confidence * 100).toFixed(1)}%</span>
            </p>
            <p className="text-gray-500 text-sm mt-1">Duration: {result.duration_seconds}s</p>
          </div>

          {/* Spectrogram */}
          {result.spectrogram && result.spectrogram.data.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Spectrogram Analysis</h3>
              <Spectrogram data={result.spectrogram} />
            </div>
          )}

          {/* Signal Checks */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">
              Acoustic Analysis ({result.signal_summary.checks_passed}/{result.signal_summary.checks_total} checks passed)
            </h3>
            <div className="space-y-3">
              {result.signal_checks.map((check) => (
                <div key={check.check_name} className="flex items-start gap-3 bg-dark-700/50 rounded-lg p-4">
                  {check.passed ? (
                    <CheckCircle className="w-5 h-5 text-safe flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium capitalize">{check.check_name.replace('_', ' ')}</p>
                      <span className={`text-sm font-mono ${check.score > 0.5 ? 'text-safe' : 'text-danger'}`}>
                        {(check.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mt-1">{check.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
