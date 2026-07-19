import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FileText, MessageSquare, Wrench,
  ShieldCheck, BookOpen, Activity, Menu, X, LogOut, User,
} from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const roleColors: Record<string, string> = {
  admin: 'text-red-400',
  engineer: 'text-blue-400',
  technician: 'text-green-400',
  compliance_officer: 'text-purple-400',
  viewer: 'text-gray-400',
}

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/copilot', label: 'Copilot', icon: MessageSquare },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/maintenance', label: 'Maintenance', icon: Wrench },
  { to: '/compliance', label: 'Compliance', icon: ShieldCheck },
  { to: '/lessons', label: 'Lessons', icon: BookOpen },
  { to: '/graph', label: 'Knowledge Graph', icon: Activity },
]

export default function Layout() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      {/* Sidebar — desktop */}
      <aside className="hidden md:flex flex-col w-60 bg-gray-900 border-r border-gray-800 shrink-0">
        <div className="px-5 py-4 border-b border-gray-800">
          <span className="text-blue-400 font-bold text-lg tracking-tight">IntelliPlant</span>
          <p className="text-gray-500 text-xs mt-0.5">Industrial Knowledge AI</p>
        </div>
        <nav className="flex-1 py-4 space-y-0.5 px-2 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-3 border-t border-gray-800 space-y-2">
          {user && (
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-gray-500 shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-gray-300 truncate">{user.name}</p>
                <p className={`text-xs capitalize ${roleColors[user.role] ?? 'text-gray-400'}`}>
                  {user.role.replace('_', ' ')}
                </p>
              </div>
            </div>
          )}
          <button onClick={handleLogout} className="flex items-center gap-2 text-xs text-gray-500 hover:text-red-400 transition-colors w-full">
            <LogOut className="w-3.5 h-3.5" /> Sign out
          </button>
          <p className="text-xs text-gray-700">v1.0.0 · Hackathon Demo</p>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {open && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="fixed inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="relative flex flex-col w-60 bg-gray-900 border-r border-gray-800">
            <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
              <span className="text-blue-400 font-bold text-lg">IntelliPlant</span>
              <button onClick={() => setOpen(false)}>
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <nav className="flex-1 py-4 space-y-0.5 px-2">
              {nav.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Mobile header */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800">
          <button onClick={() => setOpen(true)}>
            <Menu className="w-5 h-5 text-gray-400" />
          </button>
          <span className="text-blue-400 font-bold">IntelliPlant</span>
          <div className="w-5" />
        </header>
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
