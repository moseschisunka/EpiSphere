'use client'

import { useState, useEffect } from 'react'
import { clinicalApi, diseasesApi } from '../../lib/api'
import { toast } from 'sonner'
import {
  UserPlus, Stethoscope, X, Plus, ArrowLeft,
  Loader2, FileText, Pill, Thermometer, Activity
} from 'lucide-react'

const SYMPTOM_PRESETS = [
  'Fever', 'Cough', 'Headache', 'Diarrhea', 'Vomiting',
  'Rash', 'Fatigue', 'Body Aches', 'Sore Throat', 'Shortness of Breath',
  'Chest Pain', 'Abdominal Pain', 'Nausea', 'Loss of Appetite',
  'Night Sweats', 'Chills', 'Joint Pain', 'Runny Nose',
  'Eye Redness', 'Jaundice', 'Bleeding', 'Seizures'
]

function SymptomTagInput({ selectedSymptoms, onAdd, onRemove }: {
  selectedSymptoms: string[]
  onAdd: (symptom: string) => void
  onRemove: (symptom: string) => void
}) {
  const [query, setQuery] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)

  const filteredPresets = SYMPTOM_PRESETS.filter(
    s => s.toLowerCase().includes(query.toLowerCase()) && !selectedSymptoms.includes(s)
  )

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && query.trim()) {
      e.preventDefault()
      onAdd(query.trim())
      setQuery('')
    }
  }

  return (
    <div className="relative">
      <div className="min-h-[44px] flex flex-wrap gap-2 p-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 focus-within:ring-2 focus-within:ring-blue-500/40 focus-within:border-blue-500 transition-all">
        {selectedSymptoms.map((symptom) => (
          <span
            key={symptom}
            className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium rounded-lg border border-blue-200 dark:border-blue-800"
          >
            {symptom}
            <button
              type="button"
              onClick={() => onRemove(symptom)}
              className="hover:text-red-500 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ))}
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setShowSuggestions(true) }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder={selectedSymptoms.length === 0 ? 'Type or select symptoms...' : 'Add more...'}
          className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-gray-900 dark:text-white placeholder-gray-400"
        />
      </div>

      {/* Suggestion dropdown */}
      {showSuggestions && (query || selectedSymptoms.length === 0) && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl max-h-48 overflow-y-auto z-20">
          <div className="p-2 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase">
            Common Symptoms
          </div>
          {filteredPresets.slice(0, 10).map((symptom) => (
            <button
              key={symptom}
              type="button"
              onClick={() => { onAdd(symptom); setQuery('') }}
              className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              <Plus className="w-3.5 h-3.5 inline mr-2 text-gray-400" />
              {symptom}
            </button>
          ))}
          {filteredPresets.length === 0 && query && (
            <div className="px-3 py-2 text-sm text-gray-500">
              Press Enter to add &quot;{query}&quot;
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ClinicalDesk() {
    const [patients, setPatients] = useState<any[]>([])
    const [diseases, setDiseases] = useState<any[]>([])
    const [view, setView] = useState<'list' | 'new-patient' | 'encounter'>('list')
    const [selectedPatient, setSelectedPatient] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    // Encounter Form State
    const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([])
    const [diagnosisDiseaseId, setDiagnosisDiseaseId] = useState('')
    const [diagnosisType, setDiagnosisType] = useState<'suspected' | 'confirmed'>('suspected')
    const [rxDrug, setRxDrug] = useState('')
    const [rxDosage, setRxDosage] = useState('')
    const [rxQty, setRxQty] = useState(1)
    const [notes, setNotes] = useState('')

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        setLoading(true)
        try {
            const [pts, ds] = await Promise.all([
                clinicalApi.getPatients(),
                diseasesApi.list()
            ])
            setPatients(pts)
            setDiseases(ds)
        } catch (e) {
            console.error("Failed to load clinical data", e)
            toast.error("Failed to load clinical data")
        } finally {
            setLoading(false)
        }
    }

    const handleRegisterPatient = async (e: React.FormEvent) => {
        e.preventDefault()
        setSubmitting(true)
        const form = e.target as HTMLFormElement
        const data = {
            mrn: (form.elements.namedItem('mrn') as HTMLInputElement).value,
            gender: (form.elements.namedItem('gender') as HTMLSelectElement).value,
            dob: (form.elements.namedItem('dob') as HTMLInputElement).value
        }

        try {
            await clinicalApi.createPatient(data)
            toast.success("Patient registered successfully")
            await loadData()
            setView('list')
        } catch (e) {
            toast.error("Failed to create patient")
        } finally {
            setSubmitting(false)
        }
    }

    const handleCreateEncounter = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedPatient) return
        setSubmitting(true)

        const encounterData = {
            patient_id: selectedPatient.id,
            symptoms: selectedSymptoms,
            notes: notes || undefined,
            diagnoses: diagnosisDiseaseId ? [{
                disease_id: parseInt(diagnosisDiseaseId),
                diagnosis_type: diagnosisType
            }] : [],
            prescriptions: rxDrug ? [{
                drug_name: rxDrug,
                dosage: rxDosage || undefined,
                quantity: rxQty
            }] : []
        }

        try {
            await clinicalApi.createEncounter(encounterData)
            toast.success("Clinical visit recorded successfully")
            setView('list')
            // Reset form
            setSelectedSymptoms([])
            setDiagnosisDiseaseId('')
            setDiagnosisType('suspected')
            setRxDrug('')
            setRxDosage('')
            setRxQty(1)
            setNotes('')
        } catch (e) {
            toast.error("Failed to record clinical encounter")
        } finally {
            setSubmitting(false)
        }
    }

    const addSymptom = (symptom: string) => {
        if (!selectedSymptoms.includes(symptom)) {
            setSelectedSymptoms(prev => [...prev, symptom])
        }
    }

    const removeSymptom = (symptom: string) => {
        setSelectedSymptoms(prev => prev.filter(s => s !== symptom))
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
            <main className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
                                <Stethoscope className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                            </div>
                            Clinical Desk
                        </h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-1">Patient management and encounter recording</p>
                    </div>
                    {view === 'list' ? (
                        <button
                            onClick={() => setView('new-patient')}
                            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm"
                        >
                            <UserPlus className="w-4 h-4" />
                            Register Patient
                        </button>
                    ) : (
                        <button
                            onClick={() => setView('list')}
                            className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-4 py-2 rounded-lg transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back to Patients
                        </button>
                    )}
                </div>

                {/* Patient List View */}
                {view === 'list' && (
                    <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
                        {loading ? (
                            <div className="flex items-center justify-center p-12">
                                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                                <span className="ml-3 text-gray-500">Loading patients...</span>
                            </div>
                        ) : patients.length === 0 ? (
                            <div className="text-center py-16 px-6">
                                <UserPlus className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">No patients found</h3>
                                <p className="text-gray-500 dark:text-gray-400">Register a patient to begin recording clinical encounters.</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="min-w-full">
                                    <thead>
                                        <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">MRN</th>
                                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date of Birth</th>
                                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Gender</th>
                                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                        {patients.map(p => (
                                            <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                                                <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{p.mrn_display || 'Protected'}</td>
                                                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">{p.dob}</td>
                                                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">
                                                    <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                                                        {p.gender === 'M' ? 'Male' : p.gender === 'F' ? 'Female' : 'Other'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button
                                                        onClick={() => { setSelectedPatient(p); setView('encounter'); }}
                                                        className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                                                    >
                                                        <Activity className="w-3.5 h-3.5" />
                                                        New Visit
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* Register Patient Form */}
                {view === 'new-patient' && (
                    <div className="max-w-lg mx-auto">
                        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                                    <UserPlus className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                </div>
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Register Patient</h2>
                            </div>
                            <form onSubmit={handleRegisterPatient} className="space-y-5">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                        Medical Record Number (MRN) *
                                    </label>
                                    <input name="mrn" className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all" required />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                        Date of Birth *
                                    </label>
                                    <input name="dob" type="date" className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all" required />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Gender</label>
                                    <select name="gender" className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all">
                                        <option value="M">Male</option>
                                        <option value="F">Female</option>
                                        <option value="O">Other</option>
                                    </select>
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button type="submit" disabled={submitting} className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl font-medium transition-colors">
                                        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                                        {submitting ? 'Saving...' : 'Register'}
                                    </button>
                                    <button type="button" onClick={() => setView('list')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-4 py-2.5 rounded-xl transition-colors">
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Encounter Form */}
                {view === 'encounter' && selectedPatient && (
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
                                    <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">New Clinical Encounter</h2>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        Patient: {selectedPatient.mrn_display || 'Protected'}
                                    </p>
                                </div>
                            </div>

                            <form onSubmit={handleCreateEncounter} className="space-y-8">
                                {/* Section 1: Symptoms */}
                                <div>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Thermometer className="w-4 h-4 text-orange-500" />
                                        <h3 className="font-semibold text-gray-900 dark:text-white">Clinical Assessment</h3>
                                    </div>
                                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                        Presenting Symptoms
                                    </label>
                                    <SymptomTagInput
                                        selectedSymptoms={selectedSymptoms}
                                        onAdd={addSymptom}
                                        onRemove={removeSymptom}
                                    />
                                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1.5">
                                        Click presets or type custom symptoms. Press Enter to add.
                                    </p>
                                </div>

                                {/* Section 2: Diagnosis */}
                                <div>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Stethoscope className="w-4 h-4 text-purple-500" />
                                        <h3 className="font-semibold text-gray-900 dark:text-white">Diagnosis</h3>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Suspected Disease</label>
                                            <select
                                                value={diagnosisDiseaseId}
                                                onChange={e => setDiagnosisDiseaseId(e.target.value)}
                                                className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all"
                                            >
                                                <option value="">Select Disease (Optional)</option>
                                                {diseases.map(d => (
                                                    <option key={d.id} value={d.id}>{d.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Classification</label>
                                            <select
                                                value={diagnosisType}
                                                onChange={e => setDiagnosisType(e.target.value as 'suspected' | 'confirmed')}
                                                className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all"
                                            >
                                                <option value="suspected">Suspected</option>
                                                <option value="confirmed">Confirmed</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                {/* Section 3: Prescription */}
                                <div>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Pill className="w-4 h-4 text-teal-500" />
                                        <h3 className="font-semibold text-gray-900 dark:text-white">Treatment</h3>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                        <div className="sm:col-span-1">
                                            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Drug Name</label>
                                            <input
                                                value={rxDrug}
                                                onChange={e => setRxDrug(e.target.value)}
                                                placeholder="e.g. Amoxicillin"
                                                className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Dosage</label>
                                            <input
                                                value={rxDosage}
                                                onChange={e => setRxDosage(e.target.value)}
                                                placeholder="e.g. 500mg TDS"
                                                className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Qty</label>
                                            <input
                                                type="number"
                                                value={rxQty}
                                                onChange={e => setRxQty(parseInt(e.target.value) || 1)}
                                                min={1}
                                                className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Notes */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Clinical Notes</label>
                                    <textarea
                                        value={notes}
                                        onChange={e => setNotes(e.target.value)}
                                        rows={3}
                                        placeholder="Additional observations or notes..."
                                        className="w-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all resize-none"
                                    />
                                </div>

                                <div className="flex gap-3 pt-4 border-t border-gray-100 dark:border-gray-800">
                                    <button
                                        type="submit"
                                        disabled={submitting}
                                        className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
                                    >
                                        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                                        {submitting ? 'Recording...' : 'Record Visit'}
                                    </button>
                                    <button type="button" onClick={() => setView('list')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-4 py-2.5 rounded-xl transition-colors">
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}
