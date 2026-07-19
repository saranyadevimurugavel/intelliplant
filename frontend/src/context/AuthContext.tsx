import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../api/client'

interface User {
  id: string
  name: string
  email: string
  role: string
  area: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  permissions: Record<string, string[]>
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [permissions, setPermissions] = useState<Record<string, string[]>>({})

  useEffect(() => {
    const stored = localStorage.getItem('intelliplant_token')
    const storedUser = localStorage.getItem('intelliplant_user')
    const storedPerms = localStorage.getItem('intelliplant_perms')
    if (stored && storedUser) {
      setToken(stored)
      setUser(JSON.parse(storedUser))
      setPermissions(storedPerms ? JSON.parse(storedPerms) : {})
      api.defaults.headers.common['Authorization'] = `Bearer ${stored}`
    }
  }, [])

  const login = async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password })
    const { token: t, user: u, permissions: p } = res.data
    setToken(t)
    setUser(u)
    setPermissions(p)
    localStorage.setItem('intelliplant_token', t)
    localStorage.setItem('intelliplant_user', JSON.stringify(u))
    localStorage.setItem('intelliplant_perms', JSON.stringify(p))
    api.defaults.headers.common['Authorization'] = `Bearer ${t}`
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setPermissions({})
    localStorage.removeItem('intelliplant_token')
    localStorage.removeItem('intelliplant_user')
    localStorage.removeItem('intelliplant_perms')
    delete api.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, token, permissions, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function canAccess(permissions: Record<string, string[]>, module: string, action: string): boolean {
  return (permissions[module] ?? []).includes(action)
}
