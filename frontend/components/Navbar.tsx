'use client'

import Link from 'next/link'
import { authApi } from '../lib/api'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'

export default function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userRole, setUserRole] = useState<string | null>(null)
  const [userName, setUserName] = useState<string | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await authApi.getCurrentUser()
        if (user && user.role) {
          setIsAuthenticated(true)
          setUserRole(user.role.name)
          setUserName(user.full_name || user.email)
        }
      } catch (e) {
        setIsAuthenticated(false)
        setUserRole(null)
        setUserName(null)
      }
    }
    checkAuth()
  }, [pathname])

  const handleLogout = async () => {
    try {
      await authApi.logout()
      toast.info('Logged out successfully')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setIsAuthenticated(false)
      setUserRole(null)
      setUserName(null)
      router.push('/auth/login')
      router.refresh()
    }
  }

  const isActive = (path: string) => pathname === path

  return (
    <nav className="bg-white/95 backdrop-blur border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2 text-2xl font-black tracking-tight text-blue-600">
            <span className="bg-blue-600 text-white rounded-lg px-2 py-0.5 text-xl font-bold">E</span>
            <span>EpiSphere <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200">AI</span></span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex gap-1 items-center">
            {['admin', 'epidemiologist'].includes(userRole || '') && (
              <Link
                href="/surveillance"
                className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive('/surveillance') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                Surveillance
              </Link>
            )}
            <Link
              href="/dashboard/global"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive('/dashboard/global') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Dashboard
            </Link>
            <Link
              href="/alerts"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive('/alerts') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Alerts
            </Link>
            <Link
              href="/browse"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive('/browse') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Browse
            </Link>

            {isAuthenticated ? (
              <>
                {['clinician', 'facility_admin', 'admin'].includes(userRole || '') && (
                  <Link
                    href="/clinical"
                    className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive('/clinical') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Clinical
                  </Link>
                )}
                {['pharmacist', 'facility_admin', 'admin'].includes(userRole || '') && (
                  <Link
                    href="/pharmacy"
                    className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive('/pharmacy') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Pharmacy
                  </Link>
                )}
                {['facility_admin', 'admin'].includes(userRole || '') && (
                  <Link
                    href="/facility"
                    className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive('/facility') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Admin
                  </Link>
                )}
                <Link
                  href="/upload"
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive('/upload') ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  Upload Data
                </Link>

                <div className="h-4 w-[1px] bg-gray-200 mx-2" />

                {userRole && (
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 capitalize border border-gray-200">
                    {userRole.replace('_', ' ')}
                  </span>
                )}

                <button
                  onClick={handleLogout}
                  className="px-3 py-2 text-sm font-medium rounded-md text-red-600 hover:bg-red-50 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2 ml-2">
                <Link
                  href="/auth/login"
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-all"
                >
                  Sign In
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Hamburger Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white px-4 pt-2 pb-4 space-y-1 shadow-lg">
          <Link
            href="/dashboard/global"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
          >
            Dashboard
          </Link>
          <Link
            href="/alerts"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
          >
            Alerts
          </Link>
          <Link
            href="/browse"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
          >
            Browse
          </Link>

          {isAuthenticated ? (
            <>
              {['admin', 'epidemiologist'].includes(userRole || '') && (
                <Link
                  href="/surveillance"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
                >
                  Surveillance
                </Link>
              )}
              {['clinician', 'facility_admin', 'admin'].includes(userRole || '') && (
                <Link
                  href="/clinical"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
                >
                  Clinical Desk
                </Link>
              )}
              {['pharmacist', 'facility_admin', 'admin'].includes(userRole || '') && (
                <Link
                  href="/pharmacy"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
                >
                  Pharmacy Inventory
                </Link>
              )}
              {['facility_admin', 'admin'].includes(userRole || '') && (
                <Link
                  href="/facility"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
                >
                  Facility Admin
                </Link>
              )}
              <Link
                href="/upload"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-50"
              >
                Upload Data
              </Link>
              <button
                onClick={() => {
                  setMobileMenuOpen(false)
                  handleLogout()
                }}
                className="w-full text-left block px-3 py-2 rounded-md text-base font-medium text-red-600 hover:bg-red-50"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              href="/auth/login"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-center mt-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-medium"
            >
              Sign In
            </Link>
          )}
        </div>
      )}
    </nav>
  )
}
