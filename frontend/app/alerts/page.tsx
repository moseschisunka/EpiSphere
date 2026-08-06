'use client'

import { useEffect, useState } from 'react'
import { alertsApi } from '@/lib/api'
import Link from 'next/link'
import { toast } from 'sonner'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
  })

  useEffect(() => {
    loadAlerts()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters])

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (filters.severity) params.severity = filters.severity
      if (filters.status) params.status_filter = filters.status
      
      const data = await alertsApi.list(params)
      setAlerts(data)
    } catch (error) {
      console.error('Error loading alerts:', error)
      toast.error('Failed to load outbreak alerts')
    } finally {
      setLoading(false)
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return 'bg-red-50 text-red-700 border-red-200'
      case 'moderate':
        return 'bg-amber-50 text-amber-700 border-amber-200'
      case 'low':
        return 'bg-blue-50 text-blue-700 border-blue-200'
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'triggered':
        return 'bg-rose-100 text-rose-800 border-rose-300'
      case 'investigating':
        return 'bg-sky-100 text-sky-800 border-sky-300'
      case 'resolved':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      alert.country_name?.toLowerCase().includes(q) ||
      alert.disease_name?.toLowerCase().includes(q) ||
      alert.explanation?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Outbreak Intelligence & Alerts</h1>
          <p className="text-gray-500 text-sm mt-1">Real-time epidemiological anomaly detection signals across regions</p>
        </div>
        <button
          onClick={loadAlerts}
          className="self-start md:self-auto px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 shadow-sm flex items-center gap-2 transition-all"
        >
          <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Alerts
        </button>
      </div>

      <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 mb-8">
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Search Alerts
            </label>
            <input
              type="text"
              placeholder="Search by country, disease, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="border border-gray-200 rounded-lg px-4 py-2 text-sm w-full focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Filter by Severity
            </label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="border border-gray-200 rounded-lg px-4 py-2 text-sm w-full focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
            >
              <option value="">All Severities</option>
              <option value="low">Low Risk</option>
              <option value="moderate">Moderate Risk</option>
              <option value="high">High Risk</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Filter by Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="border border-gray-200 rounded-lg px-4 py-2 text-sm w-full focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
            >
              <option value="">All Statuses</option>
              <option value="triggered">Triggered</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm animate-pulse space-y-3">
              <div className="h-6 bg-gray-200 rounded w-1/3" />
              <div className="h-4 bg-gray-100 rounded w-3/4" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-gray-100 shadow-sm text-center">
          <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-bold text-gray-800">No Outbreak Alerts Found</h3>
          <p className="text-gray-500 text-sm mt-1">Try resetting your search query or severity filters.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => {
            const probPercent = Math.round((alert.probability_score || 0) * 100)
            return (
              <div key={alert.id} className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex flex-col md:flex-row justify-between md:items-center mb-4 gap-2">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">
                      {alert.country_name} — <span className="text-blue-600">{alert.disease_name}</span>
                    </h3>
                    <p className="text-gray-400 text-xs mt-0.5">
                      Triggered: {new Date(alert.triggered_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getSeverityBadge(alert.severity)}`}>
                      {alert.severity?.toUpperCase()} RISK
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusBadge(alert.status)}`}>
                      {alert.status?.toUpperCase()}
                    </span>
                  </div>
                </div>

                <p className="text-gray-700 text-sm mb-4 leading-relaxed bg-gray-50/50 p-3 rounded-lg border border-gray-100">
                  {alert.explanation}
                </p>

                <div className="mb-4">
                  <div className="flex justify-between items-center text-xs text-gray-500 mb-1">
                    <span>Probability Confidence Score</span>
                    <span className="font-bold text-gray-800">{probPercent}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        probPercent > 75 ? 'bg-red-500' : probPercent > 40 ? 'bg-amber-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${probPercent}%` }}
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pt-3 border-t border-gray-100 gap-2 text-xs text-gray-500">
                  <div>
                    Detection Engine: <span className="font-semibold text-gray-700">{alert.detection_method}</span>
                  </div>
                  <Link
                    href={`/dashboard/country/${alert.country_id}`}
                    className="text-blue-600 hover:text-blue-800 font-bold text-sm flex items-center gap-1"
                  >
                    View Country Dashboard &rarr;
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

