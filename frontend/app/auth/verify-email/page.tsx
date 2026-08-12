'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { authApi } from '@/lib/api'

export default function VerifyEmailPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('Verifying your email address…')

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token')
    if (!token) {
      setStatus('error')
      setMessage('The verification link is missing its token.')
      return
    }
    authApi.verifyEmail(token)
      .then(() => {
        setStatus('success')
        setMessage('Your email address is verified. You can now sign in.')
      })
      .catch((error) => {
        setStatus('error')
        setMessage(error.response?.data?.detail || 'This verification link is invalid or expired.')
      })
  }, [])

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-xl">
        <h1 className="text-2xl font-bold text-slate-900">Email verification</h1>
        <p className={`mt-4 text-sm ${status === 'error' ? 'text-red-700' : 'text-slate-600'}`}>{message}</p>
        {status !== 'loading' && (
          <Link href="/auth/login" className="mt-6 inline-block rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white">
            Continue to sign in
          </Link>
        )}
      </section>
    </main>
  )
}
