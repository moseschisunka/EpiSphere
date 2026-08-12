'use client'

import { useState, useEffect } from 'react'
import { facilitiesApi } from '../../lib/api'

export default function FacilityAdmin() {
    const [facilities, setFacilities] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        facilitiesApi.list()
            .then(setFacilities)
            .catch(() => setError('Unable to load facilities. Please try again.'))
            .finally(() => setLoading(false))
    }, [])

    return (
        <div className="min-h-screen bg-gray-50">
            <main className="container mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Facility Directory</h1>
                <p className="text-gray-600 mb-6">Review the facilities available to your authorized account.</p>

                <div className="bg-white rounded-lg shadow p-6">
                    {loading && <p className="text-gray-500">Loading facilities...</p>}
                    {error && <p className="text-red-600">{error}</p>}
                    {!loading && !error && facilities.length === 0 && (
                        <p className="text-gray-500">No facilities are assigned to this account.</p>
                    )}
                    {!loading && !error && facilities.length > 0 && (
                        <ul className="divide-y">
                            {facilities.map(f => (
                                <li key={f.id} className="py-3">
                                    <strong>{f.name}</strong>
                                    <span className="text-gray-500"> ({f.type})</span>
                                    <div className="text-sm text-gray-600">{f.location || 'Location not recorded'}</div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </main>
        </div>
    )
}
