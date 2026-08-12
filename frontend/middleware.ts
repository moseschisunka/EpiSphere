import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Add paths that don't require authentication
const publicPaths = [
  '/',
  '/auth/login',
  '/auth/register',
  '/auth/mfa',
  '/auth/verify-email',
  '/auth/reset-password',
  '/browse',
  '/public/dashboard',
];

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // Check if path is public
  const isPublicPath = publicPaths.includes(path) || path.startsWith('/_next') || path.startsWith('/api/') || path.includes('.');

  // Get token from cookies
  const token = request.cookies.get('token')?.value;

  // API Proxy: Inject Authorization header and forward to backend
  if (path.startsWith('/api/v1/')) {
    const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiBaseUrl = rawApiUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');
    const destinationPath = path.replace('/api/v1', '');
    const url = new URL(`${apiBaseUrl}/api/v1${destinationPath}`);
    url.search = request.nextUrl.search;
    
    const requestHeaders = new Headers(request.headers);
    if (token) {
      requestHeaders.set('Authorization', `Bearer ${token}`);
    }
    
    return NextResponse.rewrite(url, {
      request: {
        headers: requestHeaders,
      },
    });
  }

  // Redirect to login if path is protected and there is no token
  if (!isPublicPath && !token) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }

  // Redirect away from auth pages if user is already logged in
  if (token && (path === '/auth/login' || path === '/auth/register')) {
    return NextResponse.redirect(new URL('/dashboard/global', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
