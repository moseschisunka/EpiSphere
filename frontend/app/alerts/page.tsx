'use client'

import { useEffect, useState } from 'react'
import { alertsApi } from '@/lib/api'
import type { AlertStatus } from '@/lib/api-contract'
import Link from 'next/link'
import { toast } from 'sonner'
import { Search, Filter, RefreshCw, AlertTriangle, ChevronRight, Activity } from 'lucide-react'
import clsx from 'clsx'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [updatingAlertId, setUpdatingAlertId] = useState<number | null>(null)
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

  const updateAlert = async (alertId: number, nextStatus: AlertStatus) => {
    const resolutionNotes = nextStatus === 'resolved' || nextStatus === 'false_positive'
      ? window.prompt('Add resolution notes (optional):') || undefined
      : undefined

    setUpdatingAlertId(alertId)
    try {
      const updated = await alertsApi.resolve(alertId, {
        status: nextStatus,
        resolution_notes: resolutionNotes,
      })
      setAlerts((current) => current.map((alert) => alert.id === alertId ? updated : alert))
      toast.success(`Alert marked ${nextStatus.replace('_', ' ')}`)
    } catch (error) {
      console.error('Error updating alert:', error)
      toast.error('Unable to update alert. Refresh and try again.')
    } finally {
      setUpdatingAlertId(null)
    }
  }

  const getSeverityStyles = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return {
          card: 'border-red-200 dark:border-red-900/50 bg-red-50/10',
          badge: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border-red-200 dark:border-red-800/50',
          icon: 'text-red-600 dark:text-red-500',
          progress: 'bg-red-500'
        }
      case 'moderate':
        return {
          card: 'border-amber-200 dark:border-amber-900/50 bg-amber-50/10',
          badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800/50',
          icon: 'text-amber-600 dark:text-amber-500',
          progress: 'bg-amber-500'
        }
      case 'low':
        return {
          card: 'border-teal-200 dark:border-teal-900/50 bg-teal-50/10',
          badge: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300 border-teal-200 dark:border-teal-800/50',
          icon: 'text-teal-600 dark:text-teal-500',
          progress: 'bg-teal-500'
        }
      default:
        return {
          card: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-900',
          badge: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700',
          icon: 'text-gray-500 dark:text-gray-400',
          progress: 'bg-gray-400'
        }
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'triggered':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-800/50">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-600"></span>
            </span>
            TRIGGERED
          </div>
        )
      case 'investigating':
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-900/30 dark:text-sky-300 dark:border-sky-800/50">INVESTIGATING</span>
      case 'acknowledged':
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-indigo-100 text-indigo-800 border-indigo-300 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800/50">ACKNOWLEDGED</span>
      case 'escalated':
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800/50">ESCALATED</span>
      case 'resolved':
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800/50">RESOLVED</span>
      case 'false_positive':
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">FALSE POSITIVE</span>
      case 'closed':
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700">CLOSED</span>
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold border bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">{status?.toUpperCase()}</span>
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
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 dark:text-white tracking-tight flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-600 dark:text-blue-500" />
            Outbreak Intelligence
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">Real-time epidemiological anomaly detection signals across regions</p>
        </div>
        <button
          onClick={loadAlerts}
          className="self-start md:self-auto px-4 py-2.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 shadow-sm flex items-center gap-2 transition-all"
        >
          <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
          Refresh Alerts
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 p-5 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 mb-8 transition-colors">
        <div className="grid md:grid-cols-3 gap-4">
          <div className="relative">
            <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Search className="w-3.5 h-3.5" /> Search
            </label>
            <input
              type="text"
              placeholder="Country, disease, keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white rounded-lg px-4 py-2.5 text-sm w-full focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5" /> Severity
            </label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white rounded-lg px-4 py-2.5 text-sm w-full focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all appearance-none"
            >
              <option value="">All Severities</option>
              <option value="low">Low Risk</option>
              <option value="moderate">Moderate Risk</option>
              <option value="high">High Risk</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" /> Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white rounded-lg px-4 py-2.5 text-sm w-full focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all appearance-none"
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
            <div key={i} className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-gray-100 dark:border-slate-800 shadow-sm animate-pulse space-y-4">
              <div className="flex justify-between">
                <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded w-1/3" />
                <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded w-24" />
              </div>
              <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-3/4" />
              <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 p-12 rounded-xl border border-gray-200 dark:border-slate-800 shadow-sm text-center">
          <AlertTriangle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-gray-800 dark:text-white">No Outbreak Alerts Found</h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">Try adjusting your filters or search query.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => {
            const probPercent = Math.round((alert.probability_score || 0) * 100)
            const styles = getSeverityStyles(alert.severity)
            
            return (
              <div 
                key={alert.id} 
                className={clsx(
                  "p-6 rounded-xl border shadow-sm hover:shadow-md transition-all duration-300 bg-white dark:bg-slate-900",
                  styles.card
                )}
              >
                <div className="flex flex-col md:flex-row justify-between md:items-center mb-4 gap-4">
                  <div className="flex items-start gap-3">
                    <div className={clsx("p-2 rounded-lg bg-white dark:bg-slate-800 shadow-sm border border-gray-100 dark:border-slate-700 mt-1", styles.icon)}>
                      <AlertTriangle className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                        {alert.country_name} <span className="text-gray-400 dark:text-gray-600 mx-1">•</span> <span className="text-blue-600 dark:text-blue-400">{alert.disease_name}</span>
                      </h3>
                      <p className="text-gray-500 dark:text-gray-400 text-xs mt-1 font-medium">
                        Triggered: {new Date(alert.triggered_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className={clsx("px-3 py-1 rounded-full text-xs font-bold border", styles.badge)}>
                      {alert.severity?.toUpperCase()} RISK
                    </span>
                    {getStatusBadge(alert.status)}
                  </div>
                </div>

                <div className="text-gray-700 dark:text-gray-300 text-sm mb-5 leading-relaxed bg-white/50 dark:bg-slate-800/50 p-4 rounded-lg border border-gray-100 dark:border-slate-700/50 backdrop-blur-sm">
                  {alert.explanation}
                </div>

                <div className="mb-5">
                  <div className="flex justify-between items-center text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider">
                    <span>Probability Confidence Score</span>
                    <span className="text-gray-900 dark:text-white text-sm">{probPercent}%</span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden border border-gray-200 dark:border-slate-700">
                    <div
                      className={clsx("h-full rounded-full transition-all duration-1000 ease-out", styles.progress)}
                      style={{ width: `${probPercent}%` }}
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pt-4 border-t border-gray-100 dark:border-slate-800 gap-3 text-xs text-gray-500 dark:text-gray-400">
                  <div className="flex items-center gap-2">
                    <span className="uppercase tracking-wider font-bold">Detection Engine:</span> 
                    <span className="font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded">{alert.detection_method}</span>
                  </div>
                  <Link
                    href={`/dashboard/country/${alert.country_id}`}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-bold text-sm flex items-center gap-1 group transition-colors"
                  >
                    View Country Dashboard 
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>

                {alert.status !== 'resolved' && alert.status !== 'false_positive' && alert.status !== 'closed' && (
                  <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100 dark:border-slate-800">
                    {alert.status === 'triggered' && (
                      <button
                        type="button"
                        onClick={() => updateAlert(alert.id, 'investigating')}
                        disabled={updatingAlertId === alert.id}
                        className="px-3 py-2 rounded-lg bg-sky-600 text-white text-xs font-bold hover:bg-sky-700 disabled:opacity-50"
                      >
                        {updatingAlertId === alert.id ? 'Updating…' : 'Start investigation'}
                      </button>
                    )}
                    {alert.status === 'triggered' && (
                      <button
                        type="button"
                        onClick={() => updateAlert(alert.id, 'acknowledged')}
                        disabled={updatingAlertId === alert.id}
                        className="px-3 py-2 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 disabled:opacity-50"
                      >
                        Acknowledge
                      </button>
                    )}
                    {(alert.status === 'acknowledged' || alert.status === 'investigating') && (
                      <button
                        type="button"
                        onClick={() => updateAlert(alert.id, 'escalated')}
                        disabled={updatingAlertId === alert.id}
                        className="px-3 py-2 rounded-lg bg-orange-600 text-white text-xs font-bold hover:bg-orange-700 disabled:opacity-50"
                      >
                        Escalate
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => updateAlert(alert.id, alert.status === 'triggered' ? 'false_positive' : 'resolved')}
                      disabled={updatingAlertId === alert.id}
                      className="px-3 py-2 rounded-lg bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 disabled:opacity-50"
                    >
                      {alert.status === 'triggered' ? 'Mark false positive' : 'Resolve alert'}
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
