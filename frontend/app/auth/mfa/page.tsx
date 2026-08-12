'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api'
import { toast } from 'sonner'

export default function MfaPage() {
  const router = useRouter()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authApi.verifyMfa(code.trim())
      toast.success('MFA verified. Welcome back!')
      router.push('/dashboard/global')
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'MFA verification failed'
      setError(typeof detail === 'string' ? detail : 'MFA verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <form onSubmit={submit} className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-bold text-slate-900">Multi-factor verification</h1>
        <p className="mt-2 text-sm text-slate-600">Enter the six-digit code from your authenticator app.</p>
        {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="mfa-code">Authenticator code</label>
        <input
          id="mfa-code"
          inputMode="numeric"
          pattern="[0-9]{6}"
          maxLength={6}
          required
          value={code}
          onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
          className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-3 text-center text-2xl tracking-[0.4em]"
          autoFocus
        />
        <button disabled={loading || code.length !== 6} className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white disabled:opacity-50">
          {loading ? 'Verifying…' : 'Verify and continue'}
        </button>
      </form>
    </main>
  )
}
