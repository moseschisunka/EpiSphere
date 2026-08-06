'use client'

import Link from 'next/link'
import { authApi } from '../lib/api'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState, useRef } from 'react'
import { toast } from 'sonner'
import {
  Activity, BarChart3, Bell, ChevronDown, Globe, LayoutDashboard,
  LogOut, Menu, Moon, Pill, Settings, Shield, Stethoscope,
  Sun, Upload, User, Users, X, Search, Newspaper, Building2
} from 'lucide-react'

interface NavGroup {
  label: string
  icon: React.ElementType
  items: NavItem[]
  roles?: string[]
}

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  roles?: string[]
}

const navGroups: NavGroup[] = [
  {
    label: 'Intelligence',
    icon: Activity,
    items: [
      { href: '/dashboard/global', label: 'Dashboard', icon: LayoutDashboard },
      { href: '/surveillance', label: 'Surveillance', icon: Globe, roles: ['admin', 'epidemiologist'] },
      { href: '/alerts', label: 'Alerts', icon: Bell },
    ],
  },
  {
    label: 'Operations',
    icon: Building2,
    items: [
      { href: '/clinical', label: 'Clinical Desk', icon: Stethoscope, roles: ['clinician', 'facility_admin', 'admin'] },
      { href: '/pharmacy', label: 'Pharmacy', icon: Pill, roles: ['pharmacist', 'facility_admin', 'admin'] },
      { href: '/facility', label: 'Facilities', icon: Building2, roles: ['facility_admin', 'admin'] },
    ],
  },
  {
    label: 'Data',
    icon: BarChart3,
    items: [
      { href: '/browse', label: 'Browse', icon: Search },
      { href: '/upload', label: 'Upload Data', icon: Upload },
      { href: '/admin', label: 'Admin Portal', icon: Shield, roles: ['admin'] },
    ],
  },
]

function NavDropdown({ group, userRole, isAuthenticated, pathname }: {
  group: NavGroup
  userRole: string | null
  isAuthenticated: boolean
  pathname: string
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const visibleItems = group.items.filter(item => {
    if (!item.roles) return true
    if (!isAuthenticated) return false
    return item.roles.includes(userRole || '')
  })

  if (visibleItems.length === 0) return null

  const isGroupActive = visibleItems.some(item => pathname === item.href)

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
          isGroupActive
            ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
        }`}
      >
        <group.icon className="w-4 h-4" />
        {group.label}
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-52 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl py-1.5 z-50 animate-in fade-in slide-in-from-top-2">
          {visibleItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                pathname === item.href
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const isDark = document.documentElement.classList.contains('dark')
    setTheme(isDark ? 'dark' : 'light')
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    document.documentElement.classList.toggle('dark')
    localStorage.setItem('theme', newTheme)
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      aria-label="Toggle dark mode"
    >
      {theme === 'light' ? <Moon className="w-4.5 h-4.5" /> : <Sun className="w-4.5 h-4.5" />}
    </button>
  )
}

function UserDropdown({ userName, userRole, onLogout }: {
  userName: string | null
  userRole: string | null
  onLogout: () => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const initials = userName
    ? userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U'

  const roleColor: Record<string, string> = {
    admin: 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400',
    epidemiologist: 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400',
    clinician: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400',
    pharmacist: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400',
    facility_admin: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400',
    country_data_officer: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/50 dark:text-cyan-400',
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 pl-1 pr-3 py-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
          {initials}
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
      </button>

      {open && (
        <div className="absolute top-full right-0 mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-2">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">{userName || 'User'}</p>
            {userRole && (
              <span className={`inline-flex items-center mt-1.5 px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${roleColor[userRole] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}>
                {userRole.replace('_', ' ')}
              </span>
            )}
          </div>
          <div className="py-1">
            <button
              onClick={() => {
                setOpen(false)
                onLogout()
              }}
              className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

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

  // Initialize theme from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark')
    }
  }, [])

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

  const getVisibleMobileItems = () => {
    const items: NavItem[] = []
    navGroups.forEach(group => {
      group.items.forEach(item => {
        if (!item.roles) {
          items.push(item)
        } else if (isAuthenticated && item.roles.includes(userRole || '')) {
          items.push(item)
        }
      })
    })
    return items
  }

  return (
    <nav className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/60 dark:border-gray-800/60 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 shrink-0">
            <span className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-xl px-2.5 py-1 text-lg font-bold shadow-sm">E</span>
            <span className="text-xl font-black tracking-tight text-gray-900 dark:text-white">
              EpiSphere
              <span className="ml-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 align-top">
                AI
              </span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-1">
            {navGroups.map((group) => (
              <NavDropdown
                key={group.label}
                group={group}
                userRole={userRole}
                isAuthenticated={isAuthenticated}
                pathname={pathname}
              />
            ))}
          </div>

          {/* Desktop Right Controls */}
          <div className="hidden lg:flex items-center gap-2">
            <ThemeToggle />

            {isAuthenticated ? (
              <UserDropdown
                userName={userName}
                userRole={userRole}
                onLogout={handleLogout}
              />
            ) : (
              <div className="flex items-center gap-2 ml-2">
                <Link
                  href="/auth/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/auth/register"
                  className="px-4 py-2 text-sm font-semibold rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-sm transition-all"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Controls */}
          <div className="lg:hidden flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <>
          <div className="fixed inset-0 top-16 bg-black/30 backdrop-blur-sm z-40 lg:hidden" onClick={() => setMobileMenuOpen(false)} />
          <div className="lg:hidden absolute top-16 left-0 right-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-xl z-50 max-h-[calc(100vh-4rem)] overflow-y-auto">
            <div className="container mx-auto px-4 py-4 space-y-1">
              {navGroups.map((group) => {
                const visibleItems = group.items.filter(item => {
                  if (!item.roles) return true
                  if (!isAuthenticated) return false
                  return item.roles.includes(userRole || '')
                })
                if (visibleItems.length === 0) return null
                return (
                  <div key={group.label}>
                    <div className="px-3 py-2 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                      {group.label}
                    </div>
                    {visibleItems.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                          pathname === item.href
                            ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                      >
                        <item.icon className="w-4 h-4" />
                        {item.label}
                      </Link>
                    ))}
                  </div>
                )
              })}

              <div className="border-t border-gray-100 dark:border-gray-800 pt-3 mt-3">
                {isAuthenticated ? (
                  <>
                    <div className="px-3 py-2 mb-2">
                      <p className="font-semibold text-sm text-gray-900 dark:text-white">{userName || 'User'}</p>
                      {userRole && (
                        <span className="inline-flex mt-1 px-2 py-0.5 rounded-full text-xs font-semibold capitalize bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                          {userRole.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setMobileMenuOpen(false)
                        handleLogout()
                      }}
                      className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </>
                ) : (
                  <div className="space-y-2 px-3">
                    <Link
                      href="/auth/login"
                      onClick={() => setMobileMenuOpen(false)}
                      className="block w-full text-center py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/auth/register"
                      onClick={() => setMobileMenuOpen(false)}
                      className="block w-full text-center py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 text-white"
                    >
                      Get Started
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </nav>
  )
}
