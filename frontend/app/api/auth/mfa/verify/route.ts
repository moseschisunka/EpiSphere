import { NextRequest, NextResponse } from 'next/server'
import { rejectCrossSiteMutation } from '@/lib/server/csrf'

export async function POST(request: NextRequest) {
  const csrfFailure = rejectCrossSiteMutation(request)
  if (csrfFailure) {
    return csrfFailure
  }
  const challenge = request.cookies.get('mfa_challenge')?.value
  if (!challenge) {
    return NextResponse.json({ detail: 'MFA challenge is missing or expired' }, { status: 401 })
  }

  const body = await request.json()
  const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const apiBaseUrl = rawApiUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '')
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/mfa/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ challenge_token: challenge, code: body.code }),
  })
  const data = await response.json()
  if (!response.ok) {
    return NextResponse.json(data, { status: response.status })
  }

  const nextResponse = NextResponse.json({ success: true })
  nextResponse.cookies.set('token', data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 30 * 60,
  })
  nextResponse.cookies.set('mfa_challenge', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/',
    expires: new Date(0),
  })
  return nextResponse
}
