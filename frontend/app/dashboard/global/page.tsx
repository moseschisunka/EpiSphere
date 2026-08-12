'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { RefreshCw, Filter } from 'lucide-react'
import StatsCards from '@/components/dashboard/StatsCards'
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart'
import { dashboardApi, diseasesApi } from '@/lib/api'

// Dynamic import for Leaflet map to avoid SSR issues
const GlobalMap = dynamic(() => import('@/components/dashboard/GlobalMap'), { 
  ssr: false,
  loading: () => <div className="h-[500px] w-full rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse flex items-center justify-center text-slate-500 dark:text-slate-400">Loading map...</div>
})

interface GlobalDashboardData {
  global_stats: {
    total_cases: number
    total_deaths: number
    total_countries: number
    active_diseases: number
    active_alerts: number
    latest_data_date?: string | null
    data_completeness?: number | null
    median_reporting_lag_days?: number | null
  }
  country_stats: Array<{
    country_id: number
    country_name: string
    iso_code: string
    total_cases: number
    total_deaths: number
    latitude?: number | null
    longitude?: number | null
  }>
  time_series: Array<{ date: string; value: number }>
}

function getDateRange(range: string) {
  const end = new Date()
  const start = new Date(end)
  if (range === '7d') start.setDate(end.getDate() - 6)
  else if (range === '30d') start.setDate(end.getDate() - 29)
  else if (range === '90d') start.setDate(end.getDate() - 89)
  else if (range === '1y') start.setDate(end.getDate() - 364)
  else start.setFullYear(end.getFullYear() - 10)
  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
  }
}

export default function GlobalDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<GlobalDashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('30d')
  const [diseaseFilter, setDiseaseFilter] = useState('all')
  const [diseases, setDiseases] = useState<Array<{ id: number; name: string }>>([])
  const [showMoreCountries, setShowMoreCountries] = useState(false)

  useEffect(() => {
    diseasesApi.list()
      .then(setDiseases)
      .catch(() => setDiseases([]))
  }, [])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string | number> = getDateRange(timeRange)
      if (diseaseFilter !== 'all') params.disease_id = Number(diseaseFilter)
      const response = await dashboardApi.getGlobal(params)
      setData(response)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setError('Unable to load current surveillance data. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [diseaseFilter, timeRange])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const timeRanges = [
    { value: '7d', label: '7d' },
    { value: '30d', label: '30d' },
    { value: '90d', label: '90d' },
    { value: '1y', label: '1y' },
    { value: 'all', label: 'All' }
  ]

  const visibleCountries = showMoreCountries
    ? data?.country_stats?.slice(0, 20)
    : data?.country_stats?.slice(0, 5)

  if (loading && !data) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center mb-6">
          <div className="h-10 w-64 bg-slate-200 dark:bg-slate-800 rounded-lg animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="h-80 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse"></div>
            <div className="h-[500px] bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse"></div>
          </div>
          <div className="h-[600px] bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse"></div>
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="p-6 max-w-2xl mx-auto text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Global Dashboard</h1>
        <p className="mt-3 text-red-600 dark:text-red-400">{error}</p>
        <button onClick={fetchData} className="mt-5 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700">
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 bg-slate-50 dark:bg-slate-950 min-h-screen text-slate-900 dark:text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Global Dashboard</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Current disease surveillance across reporting regions
            {data?.global_stats.latest_data_date ? ` · Latest data ${data.global_stats.latest_data_date}` : ''}
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <Filter className="w-4 h-4 text-slate-400" />
            </div>
            <select
              value={diseaseFilter}
              onChange={(e) => setDiseaseFilter(e.target.value)}
              className="pl-9 pr-8 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:text-white appearance-none cursor-pointer"
            >
              <option value="all">All Diseases</option>
              {diseases.map((disease) => (
                <option key={disease.id} value={disease.id}>{disease.name}</option>
              ))}
            </select>
          </div>
          
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
            title="Refresh data"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Date Range Selector */}
      <div className="flex flex-wrap items-center gap-2 pb-2">
        {timeRanges.map(range => (
          <button
            key={range.value}
            onClick={() => setTimeRange(range.value)}
            className={`px-4 py-1.5 text-sm font-medium rounded-full transition-colors ${
              timeRange === range.value
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            {range.label}
          </button>
        ))}
      </div>

      {/* Stats Cards */}
      {data && <StatsCards stats={data.global_stats} />}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Chart */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
            <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Disease Trends</h2>
            {data && <TimeSeriesChart data={data.time_series} />}
          </div>
          
          {/* Map */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
             <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Global Distribution</h2>
             {data && <GlobalMap countryStats={data.country_stats} />}
          </div>
        </div>

        {/* Top Countries List */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 lg:h-[830px] flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Top Affected Regions</h2>
          </div>
          
          <div className="space-y-1 flex-grow overflow-y-auto pr-2">
            {visibleCountries?.map((country, idx) => (
              <div 
                key={country.country_id}
                className={`flex items-center justify-between p-3 rounded-lg transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
                  idx % 2 === 0 ? 'bg-transparent' : 'bg-slate-50/50 dark:bg-slate-800/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 font-medium w-4">{idx + 1}.</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">{country.country_name}</span>
                </div>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {country.total_cases.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
          
          {(data?.country_stats?.length ?? 0) > 5 && (
            <button 
              onClick={() => setShowMoreCountries(!showMoreCountries)}
              className="mt-6 w-full py-2.5 text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
            >
              {showMoreCountries ? 'Show Less' : 'Show More Countries'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
