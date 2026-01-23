'use client'

import { useState, useEffect } from 'react'
import Navbar from '../../components/Navbar'
import { clinicalApi, diseasesApi } from '../../lib/api'

export default function ClinicalDesk() {
    const [patients, setPatients] = useState<any[]>([])
    const [diseases, setDiseases] = useState<any[]>([])
    const [view, setView] = useState<'list' | 'new-patient' | 'encounter'>('list')
    const [selectedPatient, setSelectedPatient] = useState<any>(null)

    // Encounter Form State
    const [symptoms, setSymptoms] = useState('')
    const [diagnosisDiseaseId, setDiagnosisDiseaseId] = useState('')
    const [rxDrug, setRxDrug] = useState('')
    const [rxQty, setRxQty] = useState(1)

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            const [pts, ds] = await Promise.all([
                clinicalApi.getPatients(),
                diseasesApi.list()
            ])
            setPatients(pts)
            setDiseases(ds)
        } catch (e) {
            console.error("Failed to load clinical data", e)
        }
    }

    const handleRegisterPatient = async (e: React.FormEvent) => {
        e.preventDefault()
        // Simplified registration
        const form = e.target as HTMLFormElement
        const data = {
            mrn: (form.elements.namedItem('mrn') as HTMLInputElement).value,
            gender: (form.elements.namedItem('gender') as HTMLSelectElement).value,
            dob: (form.elements.namedItem('dob') as HTMLInputElement).value
        }

        try {
            await clinicalApi.createPatient(data)
            await loadData()
            setView('list')
        } catch (e) {
            alert("Failed to create patient")
        }
    }

    const handleCreateEncounter = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedPatient) return

        const encounterData = {
            patient_id: selectedPatient.id,
            symptoms: symptoms.split(',').map(s => s.trim()),
            diagnoses: diagnosisDiseaseId ? [{
                disease_id: parseInt(diagnosisDiseaseId),
                diagnosis_type: 'suspected'
            }] : [],
            prescriptions: rxDrug ? [{
                drug_name: rxDrug,
                quantity: rxQty
            }] : []
        }

        try {
            await clinicalApi.createEncounter(encounterData)
            alert("Encounter recorded")
            setView('list')
            // Reset form
            setSymptoms('')
            setDiagnosisDiseaseId('')
            setRxDrug('')
        } catch (e) {
            alert("Failed to record encounter")
        }
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">Clinical Desk</h1>
                    <button
                        onClick={() => setView('new-patient')}
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                    >
                        Register Patient
                    </button>
                </div>

                {view === 'list' && (
                    <div className="bg-white rounded-lg shadow">
                        <table className="min-w-full">
                            <thead>
                                <tr className="bg-gray-50 border-b">
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MRN</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DOB</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Gender</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {patients.map(p => (
                                    <tr key={p.id}>
                                        <td className="px-6 py-4">{p.mrn || 'N/A'}</td>
                                        <td className="px-6 py-4">{p.dob}</td>
                                        <td className="px-6 py-4">{p.gender}</td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => { setSelectedPatient(p); setView('encounter'); }}
                                                className="text-blue-600 hover:underline"
                                            >
                                                New Visit
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {patients.length === 0 && <p className="p-6 text-center text-gray-500">No patients found. Register one to start.</p>}
                    </div>
                )}

                {view === 'new-patient' && (
                    <div className="bg-white p-6 rounded-lg shadow max-w-lg mx-auto">
                        <h2 className="text-xl font-bold mb-4">Register Patient</h2>
                        <form onSubmit={handleRegisterPatient} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium">MRN (Medical Record Number)</label>
                                <input name="mrn" className="w-full border p-2 rounded" required />
                            </div>
                            <div>
                                <label className="block text-sm font-medium">Date of Birth</label>
                                <input name="dob" type="date" className="w-full border p-2 rounded" required />
                            </div>
                            <div>
                                <label className="block text-sm font-medium">Gender</label>
                                <select name="gender" className="w-full border p-2 rounded">
                                    <option value="M">Male</option>
                                    <option value="F">Female</option>
                                    <option value="O">Other</option>
                                </select>
                            </div>
                            <div className="flex gap-2">
                                <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
                                <button type="button" onClick={() => setView('list')} className="text-gray-600 px-4 py-2">Cancel</button>
                            </div>
                        </form>
                    </div>
                )}

                {view === 'encounter' && selectedPatient && (
                    <div className="bg-white p-6 rounded-lg shadow max-w-2xl mx-auto">
                        <h2 className="text-xl font-bold mb-4">New Encounter: {selectedPatient.mrn}</h2>
                        <form onSubmit={handleCreateEncounter} className="space-y-6">
                            {/* Symptoms */}
                            <div>
                                <h3 className="font-semibold mb-2">1. Clinical Assessment</h3>
                                <label className="block text-sm font-medium">Symptoms (comma separated)</label>
                                <input
                                    value={symptoms}
                                    onChange={e => setSymptoms(e.target.value)}
                                    placeholder="e.g. Fever, Cough, Headache"
                                    className="w-full border p-2 rounded"
                                />
                            </div>

                            {/* Diagnosis */}
                            <div>
                                <h3 className="font-semibold mb-2">2. Diagnosis</h3>
                                <label className="block text-sm font-medium">Suspected Disease</label>
                                <select
                                    value={diagnosisDiseaseId}
                                    onChange={e => setDiagnosisDiseaseId(e.target.value)}
                                    className="w-full border p-2 rounded"
                                >
                                    <option value="">Select Disease (Optional)</option>
                                    {diseases.map(d => (
                                        <option key={d.id} value={d.id}>{d.name}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Prescription */}
                            <div>
                                <h3 className="font-semibold mb-2">3. Treatment</h3>
                                <div className="flex gap-2">
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium">Drug Name</label>
                                        <input
                                            value={rxDrug}
                                            onChange={e => setRxDrug(e.target.value)}
                                            className="w-full border p-2 rounded"
                                        />
                                    </div>
                                    <div className="w-24">
                                        <label className="block text-sm font-medium">Qty</label>
                                        <input
                                            type="number"
                                            value={rxQty}
                                            onChange={e => setRxQty(parseInt(e.target.value))}
                                            className="w-full border p-2 rounded"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-2 pt-4 border-t">
                                <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">Record Visit</button>
                                <button type="button" onClick={() => setView('list')} className="text-gray-600 px-4 py-2">Cancel</button>
                            </div>
                        </form>
                    </div>
                )}
            </main>
        </div>
    )
}
