import React, { useRef, useEffect } from 'react'

/**
 * Spectrogram visualization component.
 * Renders a mel-spectrogram as a color-coded heatmap on a canvas.
 */
export default function Spectrogram({ data }) {
  const canvasRef = useRef(null)
  
  useEffect(() => {
    if (!data || !data.data || data.data.length === 0) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    
    const nMels = data.n_mels
    const nFrames = data.n_frames
    
    // Set canvas dimensions
    const width = Math.min(800, nFrames * 4)
    const height = nMels * 3
    canvas.width = width
    canvas.height = height
    
    const cellWidth = width / nFrames
    const cellHeight = height / nMels
    
    // Draw spectrogram (flip vertically — low frequencies at bottom)
    for (let mel = 0; mel < nMels; mel++) {
      for (let frame = 0; frame < nFrames; frame++) {
        const value = data.data[mel][frame]
        const color = getColor(value)
        ctx.fillStyle = color
        ctx.fillRect(
          frame * cellWidth,
          (nMels - 1 - mel) * cellHeight,
          cellWidth + 1,
          cellHeight + 1
        )
      }
    }
    
    // Add axis labels
    ctx.fillStyle = '#94a3b8'
    ctx.font = '10px monospace'
    ctx.fillText('8kHz', 2, 12)
    ctx.fillText('0Hz', 2, height - 4)
    ctx.fillText('Time →', width - 45, height - 4)
  }, [data])
  
  // Color mapping: dark blue (low energy) → red/yellow (high energy)
  function getColor(value) {
    // value is 0-1 normalized
    const v = Math.max(0, Math.min(1, value))
    
    if (v < 0.25) {
      // Dark blue to blue
      const t = v / 0.25
      return `rgb(${Math.round(t * 30)}, ${Math.round(t * 50)}, ${Math.round(50 + t * 150)})`
    } else if (v < 0.5) {
      // Blue to cyan/green
      const t = (v - 0.25) / 0.25
      return `rgb(${Math.round(30 + t * 20)}, ${Math.round(50 + t * 150)}, ${Math.round(200 - t * 50)})`
    } else if (v < 0.75) {
      // Green to yellow
      const t = (v - 0.5) / 0.25
      return `rgb(${Math.round(50 + t * 200)}, ${Math.round(200 - t * 50)}, ${Math.round(150 - t * 120)})`
    } else {
      // Yellow to red
      const t = (v - 0.75) / 0.25
      return `rgb(${Math.round(250)}, ${Math.round(150 - t * 120)}, ${Math.round(30 - t * 20)})`
    }
  }
  
  if (!data || !data.data || data.data.length === 0) {
    return <p className="text-gray-500 text-center py-4">No spectrogram data available</p>
  }
  
  return (
    <div className="overflow-x-auto rounded-lg bg-dark-900 p-2">
      <canvas 
        ref={canvasRef} 
        className="w-full rounded" 
        style={{ imageRendering: 'pixelated', maxHeight: '200px' }}
      />
      <div className="flex justify-between mt-2 text-xs text-gray-500 px-1">
        <span>Low Energy</span>
        <div className="flex gap-1">
          <span className="w-3 h-3 rounded" style={{ background: 'rgb(0, 0, 80)' }} />
          <span className="w-3 h-3 rounded" style={{ background: 'rgb(30, 100, 180)' }} />
          <span className="w-3 h-3 rounded" style={{ background: 'rgb(50, 200, 100)' }} />
          <span className="w-3 h-3 rounded" style={{ background: 'rgb(250, 200, 30)' }} />
          <span className="w-3 h-3 rounded" style={{ background: 'rgb(250, 50, 10)' }} />
        </div>
        <span>High Energy</span>
      </div>
    </div>
  )
}
