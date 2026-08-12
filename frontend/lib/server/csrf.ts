import { NextRequest, NextResponse } from 'next/server'

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])

/**
 * The frontend proxy authenticates API calls with an httpOnly cookie. Require
 * an exact same-origin browser request before forwarding any state-changing
 * call so a third-party site cannot use that cookie for CSRF.
 */
export function rejectCrossSiteMutation(request: NextRequest): NextResponse | null {
  if (SAFE_METHODS.has(request.method.toUpperCase())) {
    return null
  }

  const origin = request.headers.get('origin')
  if (!origin || origin !== request.nextUrl.origin) {
    return NextResponse.json({ detail: 'Cross-site request rejected' }, { status: 403 })
  }
  return null
}
