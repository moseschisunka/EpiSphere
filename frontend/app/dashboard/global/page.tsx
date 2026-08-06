'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { RefreshCw, Filter } from 'lucide-react'
import StatsCards from '@/components/dashboard/StatsCards'
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart'

// Dynamic import for Leaflet map to avoid SSR issues
const GlobalMap = dynamic(() => import('@/components/dashboard/GlobalMap'), { 
  ssr: false,
  loading: () => <div className="h-[500px] w-full rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse flex items-center justify-center text-slate-500 dark:text-slate-400">Loading map...</div>
})

export default function GlobalDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>(null)
  const [timeRange, setTimeRange] = useState('30d')
  const [diseaseFilter, setDiseaseFilter] = useState('all')
  const [showMoreCountries, setShowMoreCountries] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // Mock data
      setData({
        stats: { total_cases: 12500000, total_deaths: 45000, affected_countries: 120 },
        alerts: [{ id: 1 }, { id: 2 }, { id: 3 }],
        countryStats: [
          { country_id: 1, country_name: 'United States', iso_code: 'US', total_cases: 4500000, latitude: 37.0902, longitude: -95.7129 },
          { country_id: 2, country_name: 'India', iso_code: 'IN', total_cases: 3200000, latitude: 20.5937, longitude: 78.9629 },
          { country_id: 3, country_name: 'Brazil', iso_code: 'BR', total_cases: 2800000, latitude: -14.235, longitude: -51.9253 },
          { country_id: 4, country_name: 'France', iso_code: 'FR', total_cases: 1500000, latitude: 46.2276, longitude: 2.2137 },
          { country_id: 5, country_name: 'United Kingdom', iso_code: 'GB', total_cases: 500000, latitude: 55.3781, longitude: -3.436 },
          { country_id: 6, country_name: 'Italy', iso_code: 'IT', total_cases: 450000, latitude: 41.8719, longitude: 12.5674 },
          { country_id: 7, country_name: 'Spain', iso_code: 'ES', total_cases: 400000, latitude: 40.4637, longitude: -3.7492 },
        ],
        timeSeries: Array.from({ length: 30 }).map((_, i) => {
          const date = new Date()
          date.setDate(date.getDate() - (29 - i))
          return {
            date: date.toISOString().split('T')[0],
            new_cases: Math.floor(Math.random() * 50000) + 10000,
            new_deaths: Math.floor(Math.random() * 1000) + 100
          }
        })
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [timeRange, diseaseFilter])

  const timeRanges = [
    { value: '7d', label: '7d' },
    { value: '30d', label: '30d' },
    { value: '90d', label: '90d' },
    { value: '1y', label: '1y' },
    { value: 'all', label: 'All' }
  ]

  const visibleCountries = showMoreCountries 
    ? data?.countryStats?.slice(0, 20) 
    : data?.countryStats?.slice(0, 5)

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

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 bg-slate-50 dark:bg-slate-950 min-h-screen text-slate-900 dark:text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Global Dashboard</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Real-time disease surveillance across regions</p>
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
              <option value="covid-19">COVID-19</option>
              <option value="influenza">Influenza</option>
              <option value="dengue">Dengue</option>
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
      {data && <StatsCards stats={data.stats} alerts={data.alerts} />}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Chart */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
            <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Disease Trends</h2>
            {data && <TimeSeriesChart data={data.timeSeries} />}
          </div>
          
          {/* Map */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
             <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Global Distribution</h2>
             {data && <GlobalMap countryStats={data.countryStats} />}
          </div>
        </div>

        {/* Top Countries List */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 lg:h-[830px] flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Top Affected Regions</h2>
          </div>
          
          <div className="space-y-1 flex-grow overflow-y-auto pr-2">
            {visibleCountries?.map((country: any, idx: number) => (
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
          
          {data?.countryStats?.length > 5 && (
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
