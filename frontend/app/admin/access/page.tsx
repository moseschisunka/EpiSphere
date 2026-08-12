'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Building2, Loader2, Save, ShieldCheck, Users } from 'lucide-react'
import { toast } from 'sonner'

import { authApi, facilitiesApi, interopApi, usersApi } from '@/lib/api'
import type { ApiSchemas, CurrentUser, Facility } from '@/lib/api-contract'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'

type UserRecord = CurrentUser
type RoleRecord = ApiSchemas['RoleResponse']
type FacilityRecord = Facility
type SourceRecord = ApiSchemas['SourceSystemResponse']

export default function AdminAccessPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [users, setUsers] = useState<UserRecord[]>([])
  const [roles, setRoles] = useState<RoleRecord[]>([])
  const [facilities, setFacilities] = useState<FacilityRecord[]>([])
  const [sources, setSources] = useState<SourceRecord[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)

  const selectedUser = useMemo(
    () => users.find((user) => user.id === selectedUserId) || null,
    [selectedUserId, users],
  )

  useEffect(() => {
    const load = async () => {
      try {
        const current = await authApi.getCurrentUser()
        if (!(current.roles || []).includes('admin')) {
          router.push('/')
          return
        }
        const [userRows, roleRows, facilityRows, sourceRows] = await Promise.all([
          usersApi.list(),
          usersApi.roles(),
          facilitiesApi.list(),
          interopApi.getSourceSystems(),
        ])
        setUsers(userRows)
        setRoles(roleRows)
        setFacilities(facilityRows)
        setSources(sourceRows)
        if (userRows.length) setSelectedUserId(userRows[0].id)
      } catch {
        setError('Unable to load administrator access data.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [router])

  const saveAssignment = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selectedUser) return
    const form = new FormData(event.currentTarget)
    setSaving(true)
    try {
      await usersApi.assignRole(selectedUser.id, {
        role_id: Number(form.get('role_id')),
        facility_id: form.get('facility_id') ? Number(form.get('facility_id')) : null,
        country_id: form.get('country_id') ? Number(form.get('country_id')) : null,
        is_verified: form.get('is_verified') === 'on',
      })
      const refreshed = await usersApi.list()
      setUsers(refreshed)
      toast.success('User scope and role updated')
    } catch {
      toast.error('Unable to update user assignment')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><Loader2 className="animate-spin" /> <span className="ml-2">Loading access workspace...</span></div>
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error}</div>
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-950 px-4 py-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <Button variant="ghost" onClick={() => router.push('/admin')}><ArrowLeft className="w-4 h-4 mr-2" /> Back to operations hub</Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3"><ShieldCheck className="text-blue-600" /> Access and source administration</h1>
          <p className="text-gray-500 mt-1">Assign scoped roles, review facility coverage, and verify configured ingestion identities.</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader><h2 className="font-bold flex items-center gap-2"><Users className="w-4 h-4" /> Users and roles</h2></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {users.map((user) => (
                  <button key={user.id} type="button" onClick={() => setSelectedUserId(user.id)} className={`w-full text-left p-3 rounded-lg border ${selectedUserId === user.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-800'}`}>
                    <div className="font-medium">{user.full_name || user.username}</div>
                    <div className="text-xs text-gray-500">{user.email} · {user.is_active ? 'Active' : 'Inactive'}</div>
                  </button>
                ))}
              </div>
              {selectedUser && (
                <form onSubmit={saveAssignment} className="space-y-3 border-t pt-4">
                  <label className="block text-sm font-medium">Role<select name="role_id" defaultValue={selectedUser.role_id} className="mt-1 w-full rounded-lg border p-2 bg-transparent">{roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label>
                  <label className="block text-sm font-medium">Facility<select name="facility_id" defaultValue={selectedUser.facility_id || ''} className="mt-1 w-full rounded-lg border p-2 bg-transparent"><option value="">No facility scope</option>{facilities.map((facility) => <option key={facility.id} value={facility.id}>{facility.name}</option>)}</select></label>
                  <label className="block text-sm font-medium">Country ID<input name="country_id" type="number" defaultValue={selectedUser.country_id || ''} className="mt-1 w-full rounded-lg border p-2 bg-transparent" /></label>
                  <label className="flex items-center gap-2 text-sm"><input name="is_verified" type="checkbox" defaultChecked={selectedUser.is_verified} /> Verified account</label>
                  <Button type="submit" disabled={saving}>{saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />} Save assignment</Button>
                </form>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><h2 className="font-bold flex items-center gap-2"><Building2 className="w-4 h-4" /> Facilities</h2></CardHeader>
            <CardContent><div className="space-y-2">{facilities.map((facility) => <div key={facility.id} className="flex justify-between border-b py-2 text-sm"><span>{facility.name}</span><span className="text-gray-500">Country {facility.country_id} · {facility.public_visible ? 'Public map enabled' : 'Restricted'}</span></div>)}</div></CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader><h2 className="font-bold">Configured source systems</h2></CardHeader>
          <CardContent><div className="grid md:grid-cols-2 gap-3">{sources.map((source) => <div key={source.id} className="rounded-lg border p-3"><div className="font-medium">{source.name}</div><div className="text-xs text-gray-500">{source.code} · {source.system_type} · {source.is_active ? 'Active' : 'Inactive'}</div></div>)}</div></CardContent>
        </Card>
      </div>
    </main>
  )
}
