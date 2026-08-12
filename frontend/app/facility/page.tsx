'use client'

import { useEffect, useMemo, useState } from 'react'
import { authApi, facilitiesApi } from '@/lib/api'

interface Facility {
    id: number
    name: string
    type: string
    country_id: number
    location?: string | null
    province?: string | null
    district?: string | null
    public_visible: boolean
}

interface StaffMember {
    id: number
    username: string
    email: string
    full_name?: string | null
    role_id: number
    is_active: boolean
    is_verified: boolean
    mfa_enabled: boolean
}

export default function FacilityAdmin() {
    const [facilities, setFacilities] = useState<Facility[]>([])
    const [selectedId, setSelectedId] = useState<number | null>(null)
    const [staff, setStaff] = useState<StaffMember[]>([])
    const [loading, setLoading] = useState(true)
    const [savingConsent, setSavingConsent] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const selectedFacility = useMemo(
        () => facilities.find((facility) => facility.id === selectedId) || null,
        [facilities, selectedId],
    )

    useEffect(() => {
        const load = async () => {
            try {
                const [currentUser, availableFacilities] = await Promise.all([
                    authApi.getCurrentUser(),
                    facilitiesApi.list(),
                ])
                setFacilities(availableFacilities)
                setSelectedId(currentUser.facility_id || availableFacilities[0]?.id || null)
            } catch {
                setError('Unable to load your authorized facility workspace.')
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    useEffect(() => {
        if (!selectedId) {
            setStaff([])
            return
        }
        facilitiesApi.staff(selectedId)
            .then(setStaff)
            .catch(() => setError('Unable to load facility staff.'))
    }, [selectedId])

    const toggleConsent = async () => {
        if (!selectedFacility) return
        setSavingConsent(true)
        try {
            await facilitiesApi.updateConsent(selectedFacility.id, !selectedFacility.public_visible)
            setFacilities((current) => current.map((facility) => (
                facility.id === selectedFacility.id
                    ? { ...facility, public_visible: !facility.public_visible }
                    : facility
            )))
        } catch {
            setError('Unable to update public-data consent.')
        } finally {
            setSavingConsent(false)
        }
    }

    if (loading) {
        return <main className="min-h-screen bg-gray-50 p-8 text-gray-500">Loading facility workspace…</main>
    }

    return (
        <main className="min-h-screen bg-gray-50 px-4 py-8 dark:bg-gray-950 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-6xl space-y-6">
                <header>
                    <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">Facility administration</p>
                    <h1 className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">Authorized facility workspace</h1>
                    <p className="mt-2 text-gray-600 dark:text-gray-400">Review assigned staff and control whether aggregate facility activity may appear on the public map.</p>
                </header>

                {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

                {facilities.length > 1 && (
                    <label className="block max-w-md text-sm font-medium text-gray-700 dark:text-gray-300">
                        Facility
                        <select value={selectedId || ''} onChange={(event) => setSelectedId(Number(event.target.value))} className="mt-2 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 dark:border-gray-700 dark:bg-gray-900 dark:text-white">
                            {facilities.map((facility) => <option key={facility.id} value={facility.id}>{facility.name}</option>)}
                        </select>
                    </label>
                )}

                {selectedFacility ? (
                    <>
                        <section className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-900">
                            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                                <div>
                                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{selectedFacility.name}</h2>
                                    <p className="mt-1 text-sm text-gray-500">{selectedFacility.type} · {selectedFacility.province || 'Province not recorded'} · {selectedFacility.district || 'District not recorded'}</p>
                                </div>
                                <button onClick={toggleConsent} disabled={savingConsent} className={`rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 ${selectedFacility.public_visible ? 'bg-emerald-600' : 'bg-slate-600'}`}>
                                    {savingConsent ? 'Saving…' : selectedFacility.public_visible ? 'Public map: enabled' : 'Public map: disabled'}
                                </button>
                            </div>
                            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">Only privacy-suppressed aggregate activity is eligible for public display. Patient identifiers are never exposed by this setting.</p>
                        </section>

                        <section className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-900">
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Assigned staff</h2>
                            <div className="mt-4 overflow-x-auto">
                                <table className="min-w-full text-left text-sm">
                                    <thead className="border-b border-gray-200 text-gray-500 dark:border-gray-800"><tr><th className="px-3 py-2">Name</th><th className="px-3 py-2">Email</th><th className="px-3 py-2">Account</th><th className="px-3 py-2">MFA</th></tr></thead>
                                    <tbody>
                                        {staff.map((member) => <tr key={member.id} className="border-b border-gray-100 dark:border-gray-800"><td className="px-3 py-3 font-medium text-gray-900 dark:text-white">{member.full_name || member.username}</td><td className="px-3 py-3 text-gray-600 dark:text-gray-400">{member.email}</td><td className="px-3 py-3">{member.is_active ? 'Active' : 'Inactive'}{member.is_verified ? ' · Verified' : ' · Unverified'}</td><td className="px-3 py-3">{member.mfa_enabled ? 'Enabled' : 'Not enrolled'}</td></tr>)}
                                    </tbody>
                                </table>
                                {staff.length === 0 && <p className="py-6 text-center text-sm text-gray-500">No staff are assigned to this facility.</p>}
                            </div>
                        </section>
                    </>
                ) : (
                    <section className="rounded-xl bg-white p-6 text-gray-500 shadow-sm dark:bg-gray-900">No authorized facility is assigned to this account.</section>
                )}
            </div>
        </main>
    )
}
