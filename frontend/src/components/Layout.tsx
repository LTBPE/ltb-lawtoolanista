import { NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/courts', label: 'Courts' },
  { to: '/changes', label: 'Changes' },
  { to: '/settings', label: 'Settings' },
]

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-900 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <span className="font-bold text-lg tracking-tight">LTB LawToolanista</span>
              <span className="text-blue-300 text-sm hidden sm:block">LawToolBox</span>
            </div>
            <nav className="flex gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      'px-3 py-2 rounded text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-blue-700 text-white'
                        : 'text-blue-200 hover:bg-blue-800 hover:text-white',
                    ].join(' ')
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>

      <footer className="border-t border-gray-200 bg-white py-3 text-center text-xs text-gray-400">
        LTB LawToolanista v1.0 - LawToolBox Internal Tool
      </footer>
    </div>
  )
}
