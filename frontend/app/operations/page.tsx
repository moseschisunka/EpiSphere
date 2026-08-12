'use client'

import { useCallback, useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'

type OperationsData = {
  active_alerts: number
  overdue_alerts: number
  unassigned_alerts: number
  alert_queue: Array<{ id: number; country_name: string; disease_name: string; severity: string; status: string; age_hours: number; sla_due: boolean; assigned_to?: number | null }>
  reporting_delays: Array<{ country_id: number; country_name: string; latest_data_date?: string | null; reporting_lag_days?: number | null; freshness_status: string }>
}

export default function OperationsPage() {
  const [data, setData] = useState<OperationsData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const response = await fetch('/api/v1/dashboard/operations')
      if (!response.ok) throw new Error('Unable to load operations data')
      setData(await response.json())
    } catch { setError('Unable to load the operational queue. Check your role assignment and try again.') }
    finally { setLoading(false) }
  }, [])
  useEffect(() => { load() }, [load])
  return <main className="mx-auto max-w-7xl space-y-6 p-6">
    <header className="flex items-start justify-between gap-4"><div><h1 className="text-3xl font-bold">EOC Operations</h1><p className="mt-1 text-sm text-slate-500">Authoritative alert queue, response SLAs, and reporting delays.</p></div><button onClick={load} disabled={loading} className="rounded-lg border p-2" aria-label="Refresh operations"><RefreshCw className={loading ? 'animate-spin' : ''} /></button></header>
    {error && <p className="rounded-lg bg-red-50 p-4 text-red-700">{error}</p>}
    {data && <><section className="grid gap-4 sm:grid-cols-3"><Metric label="Active alerts" value={data.active_alerts} /><Metric label="SLA overdue" value={data.overdue_alerts} danger /><Metric label="Unassigned" value={data.unassigned_alerts} /></section>
      <section className="rounded-xl border bg-white p-5 dark:bg-slate-900"><h2 className="mb-3 text-lg font-semibold">Response queue</h2><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-slate-500"><th>Alert</th><th>Severity</th><th>Status</th><th>Age</th><th>Owner</th></tr></thead><tbody>{data.alert_queue.map(a => <tr key={a.id} className="border-b"><td className="py-3">{a.country_name} · {a.disease_name}</td><td>{a.severity}</td><td>{a.status}{a.sla_due && <span className="ml-2 text-red-600">SLA due</span>}</td><td>{a.age_hours}h</td><td>{a.assigned_to ? `User #${a.assigned_to}` : 'Unassigned'}</td></tr>)}{data.alert_queue.length === 0 && <tr><td colSpan={5} className="py-6 text-center text-slate-500">No active alerts in your scope.</td></tr>}</tbody></table></div></section>
      <section className="rounded-xl border bg-white p-5 dark:bg-slate-900"><h2 className="mb-3 text-lg font-semibold">Reporting delays</h2><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{data.reporting_delays.map(item => <div key={item.country_id} className="rounded-lg border p-3"><div className="font-medium">{item.country_name}</div><div className="text-sm text-slate-500">Latest: {item.latest_data_date || 'No data'} · Lag: {item.reporting_lag_days ?? 'unknown'} days</div><div className="mt-1 text-sm font-medium capitalize">{item.freshness_status}</div></div>)}</div></section></>}
  </main>
}

function Metric({ label, value, danger = false }: { label: string; value: number; danger?: boolean }) { return <div className="rounded-xl border bg-white p-5 dark:bg-slate-900"><p className="text-sm text-slate-500">{label}</p><p className={danger ? 'mt-1 text-3xl font-bold text-red-600' : 'mt-1 text-3xl font-bold'}>{value}</p></div> }
