'use client'

import { useEffect, useState } from 'react'
import { alertsApi } from '@/lib/api'
import Link from 'next/link'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
  })

  useEffect(() => {
    loadAlerts()
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
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800'
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'triggered':
        return 'bg-orange-100 text-orange-800'
      case 'investigating':
        return 'bg-blue-100 text-blue-800'
      case 'resolved':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading alerts...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Outbreak Alerts</h1>

      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Severity
            </label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="border border-gray-300 rounded-lg px-4 py-2 w-full"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="border border-gray-300 rounded-lg px-4 py-2 w-full"
            >
              <option value="">All Statuses</option>
              <option value="triggered">Triggered</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {alerts.length === 0 ? (
          <div className="bg-white p-8 rounded-lg shadow-md text-center text-gray-500">
            No alerts found
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold">
                    {alert.country_name} - {alert.disease_name}
                  </h3>
                  <p className="text-gray-600 text-sm mt-1">
                    Triggered: {new Date(alert.triggered_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getSeverityColor(alert.severity)}`}>
                    {alert.severity.toUpperCase()}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(alert.status)}`}>
                    {alert.status.toUpperCase()}
                  </span>
                </div>
              </div>
              
              <div className="mb-4">
                <p className="text-gray-700">{alert.explanation}</p>
              </div>
              
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Detection Method: <span className="font-semibold">{alert.detection_method}</span> | 
                  Probability: <span className="font-semibold">{(alert.probability_score * 100).toFixed(1)}%</span>
                </div>
                <Link
                  href={`/dashboard/country/${alert.country_id}`}
                  className="text-blue-600 hover:text-blue-800 font-semibold"
                >
                  View Country Dashboard →
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
