'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { authApi } from '@/lib/api'

export default function ResetPasswordPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get('token'))
  }, [])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setMessage('')
    setError('')
    setLoading(true)
    try {
      if (token) {
        await authApi.resetPassword(token, password)
        setMessage('Password reset successfully. You can now sign in.')
      } else {
        await authApi.requestPasswordReset(email.trim())
        setMessage('If the account exists, reset instructions have been sent.')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to complete the password-reset request.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <form onSubmit={submit} className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-bold text-slate-900">{token ? 'Set a new password' : 'Reset your password'}</h1>
        <p className="mt-2 text-sm text-slate-600">{token ? 'Choose a strong password with at least eight characters.' : 'Enter your account email and we will send instructions if it exists.'}</p>
        {message && <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
        {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {token ? (
          <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="password">
            New password
            <input id="password" type="password" minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-3" />
          </label>
        ) : (
          <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="email">
            Account email
            <input id="email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-3" />
          </label>
        )}
        <button disabled={loading} className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white disabled:opacity-50">
          {loading ? 'Submitting…' : token ? 'Reset password' : 'Send reset instructions'}
        </button>
        <Link href="/auth/login" className="mt-5 block text-center text-sm text-blue-600 hover:underline">Return to sign in</Link>
      </form>
    </main>
  )
}
