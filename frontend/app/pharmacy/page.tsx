'use client'

import { useState, useEffect, useCallback } from 'react'
import Navbar from '../../components/Navbar'
import { pharmacyApi } from '../../lib/api'

interface Prescription {
    id: number;
    drug_name: string;
    quantity: number;
    patient_mrn?: string;
    clinician_name: string;
}

export default function PharmacyDesk() {
    const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const loadData = useCallback(async () => {
        try {
            setLoading(true)
            const data = await pharmacyApi.getPending()
            setPrescriptions(data)
            setError(null)
        } catch (e) {
            console.error("Failed to load pharmacy data", e)
            setError("Failed to load prescriptions")
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        loadData()
    }, [loadData])

    const handleDispense = async (id: number) => {
        try {
            await pharmacyApi.dispense({ prescription_id: id, notes: 'Dispensed via Pharmacy Desk' })
            // Optimistic update
            setPrescriptions(prev => prev.filter(p => p.id !== id))
        } catch (e) {
            console.error("Failed to dispense", e)
            // Ideally use a toast notification here
            setError("Failed to dispense medication")
        }
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">Pharmacy Desk</h1>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                        <span className="block sm:inline">{error}</span>
                    </div>
                )}

                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="p-4 border-b bg-gray-50">
                        <h2 className="font-semibold text-gray-700">Pending Prescriptions</h2>
                    </div>

                    {loading ? (
                        <div className="p-8 text-center">Loading...</div>
                    ) : (
                        <table className="min-w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Drug</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient MRN</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clinician</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {prescriptions.map(item => (
                                    <tr key={item.id}>
                                        <td className="px-6 py-4 font-medium">{item.drug_name}</td>
                                        <td className="px-6 py-4">{item.quantity}</td>
                                        <td className="px-6 py-4 text-gray-500">{item.patient_mrn || 'N/A'}</td>
                                        <td className="px-6 py-4 text-gray-500">{item.clinician_name}</td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => handleDispense(item.id)}
                                                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                                            >
                                                Dispense
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                    {!loading && prescriptions.length === 0 && (
                        <div className="p-8 text-center text-gray-500">
                            No pending prescriptions found.
                        </div>
                    )}
                </div>
            </main>
        </div>
    )
}
