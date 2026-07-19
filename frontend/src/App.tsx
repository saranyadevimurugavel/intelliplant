import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Copilot from './pages/Copilot'
import Documents from './pages/Documents'
import Maintenance from './pages/Maintenance'
import Compliance from './pages/Compliance'
import Lessons from './pages/Lessons'
import KnowledgeGraph from './pages/KnowledgeGraph'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="copilot" element={<Copilot />} />
        <Route path="documents" element={<Documents />} />
        <Route path="maintenance" element={<Maintenance />} />
        <Route path="compliance" element={<Compliance />} />
        <Route path="lessons" element={<Lessons />} />
        <Route path="graph" element={<KnowledgeGraph />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
