import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { LogIn, Shield, Wrench, FileText, ShieldCheck, Eye } from 'lucide-react'

const roleIcons: Record<string, any> = {
  admin: Shield,
  engineer: Wrench,
  technician: FileText,
  compliance_officer: ShieldCheck,
  viewer: Eye,
}

const roleColors: Record<string, string> = {
  admin: 'text-red-400 bg-red-950 border-red-800',
  engineer: 'text-blue-400 bg-blue-950 border-blue-800',
  technician: 'text-green-400 bg-green-950 border-green-800',
  compliance_officer: 'text-purple-400 bg-purple-950 border-purple-800',
  viewer: 'text-gray-400 bg-gray-800 border-gray-700',
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { data: demoUsers = [] } = useQuery({
    queryKey: ['demo-users'],
    queryFn: () => api.get('/auth/users').then(r => r.data),
  })

  const handleLogin = async (e?: React.FormEvent, demoEmail?: string, demoPassword?: string) => {
    e?.preventDefault()
    const loginEmail = demoEmail ?? email
    const loginPassword = demoPassword ?? password
    if (!loginEmail || !loginPassword) return

    setLoading(true)
    setError('')
    try {
      await login(loginEmail, loginPassword)
      navigate('/')
    } catch {
      setError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl grid md:grid-cols-2 gap-8 items-start">

        {/* Left — branding + login form */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-white">IntelliPlant</h1>
            <p className="text-blue-400 mt-1">Industrial Knowledge Intelligence</p>
            <p className="text-gray-500 text-sm mt-3">
              AI-powered platform for plant operations, maintenance, and compliance.
            </p>
          </div>

          <form onSubmit={handleLogin} className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-white font-semibold text-lg flex items-center gap-2">
              <LogIn className="w-5 h-5 text-blue-400" /> Sign In
            </h2>

            <div>
              <label className="text-xs text-gray-400 mb-1 block">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@intelliplant.com"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500"
              />
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        {/* Right — demo accounts */}
        <div className="space-y-3">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            Demo Accounts — click to sign in instantly
          </p>
          {demoUsers.map((u: any) => {
            const Icon = roleIcons[u.role] ?? Eye
            const colorClass = roleColors[u.role] ?? roleColors.viewer
            return (
              <button
                key={u.email}
                onClick={() => handleLogin(undefined, u.email, u.password)}
                className={`w-full text-left flex items-start gap-3 border rounded-xl p-4 transition-all hover:scale-[1.01] ${colorClass}`}
              >
                <Icon className="w-5 h-5 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{u.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-black/30 capitalize">
                      {u.role.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-xs mt-0.5 opacity-75">{u.email}</p>
                  <p className="text-xs mt-1 opacity-60">{u.description}</p>
                </div>
              </button>
            )
          })}
          <p className="text-xs text-gray-600 pt-2">
            This is a hackathon demo. All accounts have preset passwords shown above.
          </p>
        </div>

      </div>
    </div>
  )
}
