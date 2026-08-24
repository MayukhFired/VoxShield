import React, { useState, useEffect } from 'react'
import { Search, AlertTriangle, Phone, Plus, Shield, ChevronLeft, ChevronRight } from 'lucide-react'
import axios from 'axios'

export default function BlacklistPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [blacklist, setBlacklist] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [showReportForm, setShowReportForm] = useState(false)
  const [reportNumber, setReportNumber] = useState('')
  const [reportNotes, setReportNotes] = useState('')
  const [reporting, setReporting] = useState(false)
  const [reportSuccess, setReportSuccess] = useState(false)

  // Load blacklist on mount and page change
  useEffect(() => {
    loadBlacklist()
  }, [page])

  const loadBlacklist = async () => {
    try {
      const response = await axios.get(`/api/blacklist/list?page=${page}&page_size=10`)
      setBlacklist(response.data.entries)
      setTotalCount(response.data.total)
      setTotalPages(response.data.total_pages)
    } catch (err) {
      console.error('Failed to load blacklist:', err)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    try {
      const response = await axios.get(`/api/blacklist/check/${encodeURIComponent(searchQuery)}`)
      setSearchResult(response.data)
    } catch (err) {
      console.error('Search failed:', err)
    }
  }

  const handleReport = async (e) => {
    e.preventDefault()
    if (!reportNumber.trim()) return
    
    setReporting(true)
    try {
      await axios.post('/api/blacklist/report', {
        phone_number: reportNumber,
        notes: reportNotes || null,
      })
      setReportSuccess(true)
      setReportNumber('')
      setReportNotes('')
      setTimeout(() => {
        setReportSuccess(false)
        setShowReportForm(false)
      }, 2000)
      loadBlacklist()
    } catch (err) {
      console.error('Report failed:', err)
    } finally {
      setReporting(false)
    }
  }

  const getRiskBadge = (status, reportsCount) => {
    if (status === 'confirmed' || reportsCount >= 3) {
      return <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full text-xs font-medium">Confirmed Scam</span>
    } else if (reportsCount >= 1) {
      return <span className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded-full text-xs font-medium">Suspicious</span>
    }
    return <span className="bg-gray-500/20 text-gray-400 border border-gray-500/30 px-2 py-0.5 rounded-full text-xs font-medium">Unknown</span>
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Community Blacklist</h1>
          <p className="text-gray-400">Search and report scam phone numbers. Protect everyone.</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-primary-400">{totalCount}</p>
          <p className="text-gray-500 text-sm">reported numbers</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="card mb-6">
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter phone number to check..."
              className="w-full bg-dark-700 border border-dark-600 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
            />
          </div>
          <button type="submit" className="btn-primary">Check</button>
          <button 
            type="button" 
            onClick={() => setShowReportForm(!showReportForm)}
            className="bg-dark-700 hover:bg-dark-600 border border-dark-600 text-white font-medium px-4 py-3 rounded-lg transition-all flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Report
          </button>
        </form>
      </div>

      {/* Search Result */}
      {searchResult && (
        <div className={`card mb-6 border-2 ${
          searchResult.is_blacklisted
            ? searchResult.status === 'confirmed' ? 'border-red-500/30 bg-red-500/5' : 'border-yellow-500/30 bg-yellow-500/5'
            : 'border-green-500/30 bg-green-500/5'
        }`}>
          <div className="flex items-center gap-4">
            {searchResult.is_blacklisted ? (
              <AlertTriangle className={`w-10 h-10 ${searchResult.status === 'confirmed' ? 'text-danger' : 'text-warning'}`} />
            ) : (
              <Shield className="w-10 h-10 text-safe" />
            )}
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <p className="text-lg font-semibold">{searchResult.phone_number}</p>
                {searchResult.is_blacklisted && getRiskBadge(searchResult.status, searchResult.reports_count)}
              </div>
              {searchResult.is_blacklisted ? (
                <p className="text-gray-400 text-sm mt-1">
                  Reported {searchResult.reports_count} time(s) | Last: {new Date(searchResult.last_reported).toLocaleDateString()}
                </p>
              ) : (
                <p className="text-safe text-sm mt-1">This number has not been reported. Appears clean.</p>
              )}
            </div>
            {searchResult.is_blacklisted && (
              <div className="text-right">
                <p className="text-2xl font-bold text-danger">{(searchResult.avg_confidence * 100).toFixed(0)}%</p>
                <p className="text-gray-500 text-xs">avg confidence</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Report Form */}
      {showReportForm && (
        <div className="card mb-6 border border-warning/30">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-warning" />
            Report a Scam Number
          </h3>
          <form onSubmit={handleReport} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Phone Number *</label>
              <input
                type="text"
                value={reportNumber}
                onChange={(e) => setReportNumber(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Notes (optional)</label>
              <textarea
                value={reportNotes}
                onChange={(e) => setReportNotes(e.target.value)}
                placeholder="Describe the scam attempt..."
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 h-20 resize-none"
              />
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={reporting} className="btn-danger flex items-center gap-2">
                {reporting ? 'Reporting...' : 'Submit Report'}
              </button>
              {reportSuccess && <p className="text-safe self-center">Reported successfully!</p>}
            </div>
          </form>
        </div>
      )}

      {/* Blacklist Table */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Blacklisted Numbers</h3>
        {blacklist.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No numbers reported yet. Be the first to protect the community.</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-dark-700 text-gray-400 text-sm">
                    <th className="pb-3 font-medium">Phone Number</th>
                    <th className="pb-3 font-medium">Reports</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Confidence</th>
                    <th className="pb-3 font-medium">Last Reported</th>
                  </tr>
                </thead>
                <tbody>
                  {blacklist.map((entry) => (
                    <tr key={entry.id} className="border-b border-dark-700/50 hover:bg-dark-700/30">
                      <td className="py-3 flex items-center gap-2">
                        <Phone className="w-4 h-4 text-gray-500" />
                        {entry.phone_number}
                      </td>
                      <td className="py-3 font-medium">{entry.reports_count}</td>
                      <td className="py-3">{getRiskBadge(entry.status, entry.reports_count)}</td>
                      <td className="py-3">{(entry.avg_confidence * 100).toFixed(0)}%</td>
                      <td className="py-3 text-gray-400 text-sm">{new Date(entry.last_reported).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-dark-700">
                <button 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 rounded-lg hover:bg-dark-700 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-gray-400">Page {page} of {totalPages}</span>
                <button 
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 rounded-lg hover:bg-dark-700 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
