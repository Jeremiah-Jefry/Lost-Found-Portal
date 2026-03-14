import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

import LandingPage     from './pages/LandingPage'
import Dashboard       from './pages/Dashboard'
import ReportCenter    from './pages/ReportCenter'
import Feed            from './pages/Feed'
import ItemDetail      from './pages/ItemDetail'
import ReportItem      from './pages/ReportItem'
import EditItem        from './pages/EditItem'
import AdminAnalytics  from './pages/AdminAnalytics'

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/landing" replace />
  if (user.role === 'USER') return <Navigate to="/report-center" replace />
  return <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/"        element={<RootRedirect />} />
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/feed"    element={<Feed />} />
      <Route path="/items/:id" element={<ItemDetail />} />

      <Route path="/report-center" element={
        <ProtectedRoute roles={['USER', 'STAFF', 'ADMIN']}>
          <ReportCenter />
        </ProtectedRoute>
      } />

      <Route path="/report" element={
        <ProtectedRoute roles={['USER', 'STAFF', 'ADMIN']}>
          <ReportItem />
        </ProtectedRoute>
      } />

      <Route path="/items/:id/edit" element={
        <ProtectedRoute roles={['USER', 'STAFF', 'ADMIN']}>
          <EditItem />
        </ProtectedRoute>
      } />

      <Route path="/dashboard" element={
        <ProtectedRoute roles={['STAFF', 'ADMIN']}>
          <Dashboard />
        </ProtectedRoute>
      } />

      <Route path="/analytics" element={
        <ProtectedRoute roles={['ADMIN']}>
          <AdminAnalytics />
        </ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
