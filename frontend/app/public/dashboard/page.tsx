'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { publicApi } from '../../lib/api'
import PublicMap from '../../components/public/PublicMap'

export default function PublicDashboard() {
    const [stats, setStats] = useState<any>(null)
    const [alerts, setAlerts] = useState<any[]>([])

    useEffect(() => {
        publicApi.getStats().then(setStats).catch(console.error)
        publicApi.getAlerts().then(setAlerts).catch(console.error)
    }, [])

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow">
                <div className="container mx-auto px-4 py-4 flex justify-between items-center">
                    <Link href="/" className="text-2xl font-bold text-green-700">
                        EpiSphere Public
                    </Link>
                    <div className="text-sm text-gray-500">
                        Official Public Health Data Portal
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8">
                <div className="bg-blue-50 border-1-4 border-blue-500 p-4 mb-8 rounded">
                    <p className="text-blue-800 text-sm">
                        <strong>Disclaimer:</strong> Data shown here is aggregated for public assurance. It does not contain personal medical records. Consult local authorities for official guidance.
                    </p>
                </div>

                {/* Key Metrics */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-white p-6 rounded shadow text-center">
                            <div className="text-3xl font-bold text-gray-800">{stats.total_visits_recorded}</div>
                            <div className="text-gray-500 uppercase text-xs tracking-wider">Health Visits Monitored</div>
                        </div>
                        <div className="bg-white p-6 rounded shadow text-center">
                            <div className="text-3xl font-bold text-gray-800">{stats.participating_facilities}</div>
                            <div className="text-gray-500 uppercase text-xs tracking-wider">Active Facilities</div>
                        </div>
                        <div className="bg-white p-6 rounded shadow text-center">
                            <div className="text-3xl font-bold text-green-600">{stats.alert_level}</div>
                            <div className="text-gray-500 uppercase text-xs tracking-wider">National Status</div>
                        </div>
                    </div>
                )}

                {/* Alerts */}
                {alerts.length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-xl font-bold mb-4">Active Public Notices</h2>
                        <div className="space-y-4">
                            {alerts.map((a, i) => (
                                <div key={i} className="bg-orange-50 border border-orange-200 p-4 rounded text-orange-800">
                                    <strong>Notice:</strong> {a.message}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Map */}
                <section>
                    <h2 className="text-xl font-bold mb-4">Facility Activity Map</h2>
                    <div className="bg-white p-4 rounded shadow">
                        <PublicMap />
                        <p className="text-xs text-gray-400 mt-2 text-right">Only consenting facilities shown.</p>
                    </div>
                </section>

            </main>
        </div>
    )
}
