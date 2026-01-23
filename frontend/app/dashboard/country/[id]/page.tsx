'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { dashboardApi, countriesApi, diseasesApi } from '@/lib/api'
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart'

export default function CountryDashboard() {
  const params = useParams()
  const countryId = parseInt(params.id as string)
  
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [country, setCountry] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDisease, setSelectedDisease] = useState<number | null>(null)
  const [diseases, setDiseases] = useState<any[]>([])

  useEffect(() => {
    loadCountry()
    loadDiseases()
    loadDashboard()
  }, [countryId, selectedDisease])

  const loadCountry = async () => {
    try {
      const data = await countriesApi.get(countryId)
      setCountry(data)
    } catch (error) {
      console.error('Error loading country:', error)
    }
  }

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
      const data = await dashboardApi.getCountry(countryId, params)
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

  if (!dashboardData || !country) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">Error loading dashboard data</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">{country.name} Dashboard</h1>
        <p className="text-gray-600">ISO Code: {country.iso_code}</p>
        
        <div className="mt-4">
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

      {dashboardData.latest_stats && (
        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-2xl font-bold text-blue-600">
              {dashboardData.latest_stats.daily_cases?.toLocaleString() || 0}
            </div>
            <div className="text-gray-600 mt-1">Daily Cases</div>
            <div className="text-sm text-gray-500 mt-1">
              {dashboardData.latest_stats.date}
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-2xl font-bold text-purple-600">
              {dashboardData.latest_stats.cumulative_cases?.toLocaleString() || 0}
            </div>
            <div className="text-gray-600 mt-1">Cumulative Cases</div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-2xl font-bold text-red-600">
              {dashboardData.latest_stats.daily_deaths?.toLocaleString() || 0}
            </div>
            <div className="text-gray-600 mt-1">Daily Deaths</div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-2xl font-bold text-orange-600">
              {dashboardData.latest_stats.cumulative_deaths?.toLocaleString() || 0}
            </div>
            <div className="text-gray-600 mt-1">Cumulative Deaths</div>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Daily Cases Time Series</h2>
          <TimeSeriesChart 
            data={dashboardData.time_series?.map((ts: any) => ({
              date: ts.date,
              value: ts.daily_cases
            })) || []} 
          />
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">7-Day Moving Average</h2>
          <TimeSeriesChart 
            data={dashboardData.moving_averages?.map((ma: any) => ({
              date: ma.date,
              value: ma.value
            })) || []} 
          />
        </div>
      </div>

      {dashboardData.time_series && dashboardData.time_series.length > 0 && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Recent Data</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left">Date</th>
                  <th className="px-4 py-2 text-left">Daily Cases</th>
                  <th className="px-4 py-2 text-left">Cumulative Cases</th>
                  <th className="px-4 py-2 text-left">Daily Deaths</th>
                  <th className="px-4 py-2 text-left">Cumulative Deaths</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.time_series.slice(-10).reverse().map((ts: any, idx: number) => (
                  <tr key={idx} className="border-t">
                    <td className="px-4 py-2">{ts.date}</td>
                    <td className="px-4 py-2">{ts.daily_cases?.toLocaleString() || 0}</td>
                    <td className="px-4 py-2">{ts.cumulative_cases?.toLocaleString() || 0}</td>
                    <td className="px-4 py-2">{ts.daily_deaths?.toLocaleString() || 0}</td>
                    <td className="px-4 py-2">{ts.cumulative_deaths?.toLocaleString() || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
