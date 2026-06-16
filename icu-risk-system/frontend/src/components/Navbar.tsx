'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Activity, Home, Users, Shield } from 'lucide-react'
import clsx from 'clsx'

export default function Navbar() {
  const pathname = usePathname()

  const links = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/dashboard', label: 'Patients', icon: Users },
  ]

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 font-bold text-teal-700 text-lg">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            ICU Risk Monitor
          </Link>

          <div className="flex items-center gap-1">
            {links.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  pathname === href
                    ? 'bg-teal-50 text-teal-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2 text-xs text-red-600 font-medium bg-red-50 px-3 py-1.5 rounded-lg border border-red-200">
            <Shield className="w-3.5 h-3.5" />
            Demo Only
          </div>
        </div>
      </div>
    </nav>
  )
}
