'use client'

interface StatsCardsProps {
  stats: any
  alerts: any
}

export default function StatsCards({ stats, alerts }: StatsCardsProps) {
  return (
    <div className="grid md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="text-2xl font-bold text-blue-600">{stats?.total_cases?.toLocaleString() || 0}</div>
        <div className="text-gray-600 mt-1">Total Cases</div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="text-2xl font-bold text-red-600">{stats?.total_deaths?.toLocaleString() || 0}</div>
        <div className="text-gray-600 mt-1">Total Deaths</div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="text-2xl font-bold text-green-600">{stats?.active_alerts || 0}</div>
        <div className="text-gray-600 mt-1">Active Alerts</div>
        <div className="text-sm text-gray-500 mt-1">
          High: {alerts?.high || 0} | Moderate: {alerts?.moderate || 0} | Low: {alerts?.low || 0}
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="text-2xl font-bold text-purple-600">{stats?.total_countries || 0}</div>
        <div className="text-gray-600 mt-1">Countries Monitored</div>
      </div>
    </div>
  )
}
