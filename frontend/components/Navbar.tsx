'use client'

import Link from 'next/link'
import { authApi } from '../lib/api'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function Navbar() {
  const pathname = usePathname()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userRole, setUserRole] = useState<string | null>(null)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token')
      if (token) {
        setIsAuthenticated(true)
        try {
          const user = await authApi.getCurrentUser()
          setUserRole(user.role.name)
        } catch (e) {
          console.error("Failed to fetch user", e)
        }
      }
    }
    checkAuth()
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    setIsAuthenticated(false)
    window.location.href = '/'
  }

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-2xl font-bold text-blue-600">
            EpiSphere AI
          </Link>

          <div className="flex gap-4 items-center">
            {['admin', 'epidemiologist'].includes(userRole || '') && (
              <Link
                href="/surveillance"
                className={`px-3 py-2 rounded ${pathname === '/surveillance' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                  }`}
              >
                Surveillance
              </Link>
            )}
            <Link
              href="/dashboard/global"
              className={`px-3 py-2 rounded ${pathname === '/dashboard/global' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                }`}
            >
              Dashboard
            </Link>
            <Link
              href="/alerts"
              className={`px-3 py-2 rounded ${pathname === '/alerts' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                }`}
            >
              Alerts
            </Link>

            {isAuthenticated ? (
              <>
                {['clinician', 'facility_admin', 'admin'].includes(userRole || '') && (
                  <Link
                    href="/clinical"
                    className={`px-3 py-2 rounded ${pathname === '/clinical' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                      }`}
                  >
                    Clinical
                  </Link>
                )}
                {['pharmacist', 'facility_admin', 'admin'].includes(userRole || '') && (
                  <Link
                    href="/pharmacy"
                    className={`px-3 py-2 rounded ${pathname === '/pharmacy' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                      }`}
                  >
                    Pharmacy
                  </Link>
                )}
                {['facility_admin', 'admin'].includes(userRole || '') && (
                  <Link
                    href="/facility"
                    className={`px-3 py-2 rounded ${pathname === '/facility' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                      }`}
                  >
                    Admin
                  </Link>
                )}
                <Link
                  href="/upload"
                  className={`px-3 py-2 rounded ${pathname === '/upload' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                    }`}
                >
                  Upload Data
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 rounded text-gray-700 hover:bg-gray-100"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                href="/auth/login"
                className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
