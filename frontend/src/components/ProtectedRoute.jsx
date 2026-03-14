import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface">
        <i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" />
      </div>
    )
  }

  if (!user) return <Navigate to="/" state={{ from: location }} replace />

  if (roles && !roles.includes(user.role)) {
    // Redirect to appropriate home based on role
    const dest = user.role === 'USER' ? '/report-center' : '/dashboard'
    return <Navigate to={dest} replace />
  }

  return children
}
