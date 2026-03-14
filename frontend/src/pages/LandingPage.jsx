import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LandingPage() {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [form, setForm]   = useState({ username: '', email: '', password: '', password2: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let user
      if (mode === 'login') {
        user = await login(form.username, form.password)
      } else {
        if (form.password !== form.password2) {
          setError('Passwords do not match.')
          setLoading(false)
          return
        }
        user = await register(form.username, form.email, form.password, form.password2)
      }
      if (user.role === 'USER') navigate('/report-center')
      else navigate('/dashboard')
    } catch (err) {
      const data = err.response?.data
      if (data) {
        const msgs = Object.values(data).flat()
        setError(msgs.join(' '))
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4 font-sans antialiased">
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand shadow-lg shadow-blue-200/60 flex items-center justify-center mx-auto mb-4">
            <i className="fa-solid fa-magnifying-glass-location text-white text-2xl" />
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">
            KG <span className="text-brand">Recovery Portal</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1.5">Campus lost & found management system</p>
        </div>

        {/* Card */}
        <div className="card p-8">
          {/* Toggle tabs */}
          <div className="flex bg-gray-50 rounded-xl p-1 mb-6 border border-gray-100">
            {(['login', 'register']).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError('') }}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
                  mode === m ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-400 hover:text-gray-600'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
              <i className="fa-solid fa-circle-exclamation text-red-400 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">Username</label>
              <input
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                autoComplete="username"
                placeholder="Enter your username"
                className="input-field"
              />
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Email</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  placeholder="you@example.com"
                  className="input-field"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">Password</label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
                minLength={mode === 'register' ? 8 : undefined}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                placeholder={mode === 'register' ? 'Min. 8 characters' : 'Enter your password'}
                className="input-field"
              />
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Confirm Password</label>
                <input
                  type="password"
                  name="password2"
                  value={form.password2}
                  onChange={handleChange}
                  required
                  autoComplete="new-password"
                  placeholder="Re-enter password"
                  className="input-field"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <><i className="fa-solid fa-circle-notch fa-spin" /> Processing…</>
              ) : mode === 'login' ? (
                <><i className="fa-solid fa-right-to-bracket" /> Sign In</>
              ) : (
                <><i className="fa-solid fa-user-plus" /> Create Account</>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          <a href="/feed" className="text-brand hover:underline font-medium">Browse the public feed</a> without signing in
        </p>
      </div>
    </div>
  )
}
