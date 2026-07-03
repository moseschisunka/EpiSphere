'use client'

import { useEffect, useState } from 'react'
import { dashboardApi, countriesApi, diseasesApi } from '@/lib/api'
import GlobalMap from '@/components/dashboard/GlobalMap'
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart'
import StatsCards from '@/components/dashboard/StatsCards'

export default function GlobalDashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDisease, setSelectedDisease] = useState<number | null>(null)
  const [diseases, setDiseases] = useState<any[]>([])

  useEffect(() => {
    loadDiseases()
    loadDashboard()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDisease])

  const loadDiseases = async () => {
    try {
      const data = await diseasesApi.list()
      setDiseases(data)
    } catch (error) {
      console.error('Error loading diseases:', error)
    }
  }

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (selectedDisease) {
        params.disease_id = selectedDisease
      }
      const data = await dashboardApi.getGlobal(params)
      setDashboardData(data)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading dashboard...</div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">Error loading dashboard data</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">Global Surveillance Dashboard</h1>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Disease
          </label>
          <select
            value={selectedDisease || ''}
            onChange={(e) => setSelectedDisease(e.target.value ? parseInt(e.target.value) : null)}
            className="border border-gray-300 rounded-lg px-4 py-2"
          >
            <option value="">All Diseases</option>
            {diseases.map((disease) => (
              <option key={disease.id} value={disease.id}>
                {disease.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <StatsCards stats={dashboardData.global_stats} alerts={dashboardData.alerts_summary} />

      <div className="grid md:grid-cols-2 gap-6 mt-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Global Map</h2>
          <GlobalMap countryStats={dashboardData.country_stats} />
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Time Series</h2>
          <TimeSeriesChart data={dashboardData.time_series} />
        </div>
      </div>

      <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Top Countries by Cases</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left">Country</th>
                <th className="px-4 py-2 text-left">Total Cases</th>
                <th className="px-4 py-2 text-left">Total Deaths</th>
                <th className="px-4 py-2 text-left">CFR (%)</th>
                <th className="px-4 py-2 text-left">Incidence/100k</th>
              </tr>
            </thead>
            <tbody>
              {dashboardData.top_countries?.slice(0, 10).map((country: any) => (
                <tr key={country.country_id} className="border-t">
                  <td className="px-4 py-2">{country.country_name}</td>
                  <td className="px-4 py-2">{country.total_cases.toLocaleString()}</td>
                  <td className="px-4 py-2">{country.total_deaths.toLocaleString()}</td>
                  <td className="px-4 py-2">{country.cfr?.toFixed(2) || 'N/A'}</td>
                  <td className="px-4 py-2">{country.incidence_per_100k?.toFixed(2) || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

