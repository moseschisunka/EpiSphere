import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { rejectCrossSiteMutation } from '@/lib/server/csrf';

export async function POST(request: NextRequest) {
  const csrfFailure = rejectCrossSiteMutation(request);
  if (csrfFailure) {
    return csrfFailure;
  }
  const token = request.cookies.get('token')?.value;
  if (token) {
    try {
      const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const apiBaseUrl = rawApiUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');
      await fetch(`${apiBaseUrl}/api/v1/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // The cookie is still cleared locally if the backend is unavailable.
    }
  }
  const response = NextResponse.json({ success: true });
  response.cookies.set('token', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    expires: new Date(0),
  });
  return response;
}

export async function GET(request: NextRequest) {
  const response = NextResponse.redirect(new URL('/auth/login', request.url));
  response.cookies.set('token', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    expires: new Date(0),
  });
  return response;
}
