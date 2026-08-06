'use client'

import { useState, useEffect } from 'react'
import { facilitiesApi } from '../../lib/api'

// Mock user management for now as backend endpoint for "list facility users" wasn't explicitly created in this turn
// but users exist. We'll show facility details.

export default function FacilityAdmin() {
    const [facilities, setFacilities] = useState<any[]>([])

    useEffect(() => {
        facilitiesApi.list().then(setFacilities).catch(console.error)
    }, [])

    return (
        <div className="min-h-screen bg-gray-50">
            <main className="container mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">Facility Administration</h1>

                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold mb-4">Your Facilities</h2>
                    <ul>
                        {facilities.map(f => (
                            <li key={f.id} className="border-b py-2">
                                <strong>{f.name}</strong> ({f.type}) - {f.location || 'No location'}
                            </li>
                        ))}
                    </ul>
                    <p className="mt-4 text-sm text-gray-500">
                        Full user management would go here. Currently listing visible facilities.
                    </p>
                </div>
            </main>
        </div>
    )
}
