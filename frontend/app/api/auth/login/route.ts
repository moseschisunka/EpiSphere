import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log('Login request body:', body);
    
    const { username, password } = body;
    console.log('Extracted:', { username, password });

    if (!username || !password) {
      return NextResponse.json({ detail: 'Missing username or password' }, { status: 400 });
    }

    const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiBaseUrl = rawApiUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');

    // Create form data as required by OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('grant_type', 'password');
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // Create the response and set the httpOnly cookie
    const nextResponse = NextResponse.json({ success: true });
    
    nextResponse.cookies.set('token', data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 30 * 60, // 30 minutes
    });

    return nextResponse;
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { detail: 'An error occurred during login' },
      { status: 500 }
    );
  }
}
