import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

const STATUS_CLASSES = { LOST: 'bg-red-50 text-red-700 border-red-200', FOUND: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
const RESOLUTION_CLASSES = { OPEN: 'bg-blue-50 text-blue-700 border-blue-200', SECURED: 'bg-amber-50 text-amber-700 border-amber-200', RETURNED: 'bg-violet-50 text-violet-700 border-violet-200' }

export default function ItemDetail() {
  const { id }  = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [item, setItem]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [resolving, setResolving] = useState(false)
  const [resolveForm, setResolveForm] = useState({ receiver_name: '', receiver_contact: '' })
  const [showResolve, setShowResolve] = useState(false)
  const [error, setError] = useState('')

  const isOwner  = user && item && item.reporter?.id === user.id
  const isStaff  = user?.role === 'STAFF' || user?.role === 'ADMIN'
  const isAdmin  = user?.role === 'ADMIN'
  const canEdit  = isOwner || isStaff
  const canResolve = item && item.resolution_status !== 'RETURNED' && (
    isAdmin || isStaff ||
    (isOwner && item.handover_status !== 'SECURITY')
  )

  useEffect(() => {
    api.get(`/items/${id}/`).then((r) => setItem(r.data)).catch(() => navigate('/feed')).finally(() => setLoading(false))
  }, [id, navigate])

  const handleResolve = async (e) => {
    e.preventDefault()
    setResolving(true); setError('')
    try {
      const { data } = await api.post(`/items/${id}/resolve/`, resolveForm)
      setItem(data); setShowResolve(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not resolve item.')
    } finally {
      setResolving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Delete this report permanently?')) return
    await api.delete(`/items/${id}/`)
    navigate(-1)
  }

  if (loading) return (
    <Layout title="Item Detail">
      <div className="flex justify-center py-20"><i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" /></div>
    </Layout>
  )
  if (!item) return null

  return (
    <Layout title={item.title}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-6">
        <Link to="/feed" className="hover:text-brand transition-colors">Item Feed</Link>
        <i className="fa-solid fa-chevron-right text-[9px]" />
        <span className="text-gray-600 truncate max-w-xs">{item.title}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Image */}
          {item.image_url && (
            <div className="card overflow-hidden">
              <img src={item.image_url} alt={item.title} className="w-full h-72 object-cover" />
            </div>
          )}

          {/* Details card */}
          <div className="card p-6">
            <div className="flex flex-wrap items-start gap-2 mb-4">
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full border uppercase tracking-wider ${STATUS_CLASSES[item.status] || ''}`}>
                {item.status_label}
              </span>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full border uppercase tracking-wider ${RESOLUTION_CLASSES[item.resolution_status] || ''}`}>
                {item.resolution_label}
              </span>
            </div>

            <h1 className="text-xl font-extrabold text-gray-900 mb-3">{item.title}</h1>
            <p className="text-sm text-gray-600 leading-relaxed mb-5">{item.description}</p>

            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Category</dt>
                <dd className="text-gray-700 font-medium">{item.category_label}</dd>
              </div>
              <div>
                <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Location</dt>
                <dd className="text-gray-700 font-medium">{item.location}</dd>
              </div>
              <div>
                <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Reported</dt>
                <dd className="text-gray-700">{new Date(item.date_reported).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Reporter</dt>
                <dd className="text-gray-700">{item.reporter?.username || '—'}</dd>
              </div>
              {item.handover_status && (
                <div>
                  <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Handover</dt>
                  <dd className="text-gray-700">{item.handover_label}</dd>
                </div>
              )}
              {item.handover_details && (
                <div className="col-span-2">
                  <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Handover Details</dt>
                  <dd className="text-gray-700">{item.handover_details}</dd>
                </div>
              )}
              {item.receiver_name && (
                <div>
                  <dt className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Received By</dt>
                  <dd className="text-gray-700">{item.receiver_name}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Resolve form */}
          {user && canResolve && (
            <div className="card p-6">
              {!showResolve ? (
                <button
                  onClick={() => setShowResolve(true)}
                  className="w-full py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-semibold
                             hover:bg-emerald-600 transition-colors flex items-center justify-center gap-2"
                >
                  <i className="fa-solid fa-check" /> Mark as Returned to Owner
                </button>
              ) : (
                <form onSubmit={handleResolve} className="space-y-4">
                  <h3 className="text-sm font-bold text-gray-800">Confirm Return</h3>
                  {error && <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>}
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">Receiver Name (optional)</label>
                    <input
                      value={resolveForm.receiver_name}
                      onChange={(e) => setResolveForm((f) => ({ ...f, receiver_name: e.target.value }))}
                      placeholder="Full name of person collecting"
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">Contact (optional)</label>
                    <input
                      value={resolveForm.receiver_contact}
                      onChange={(e) => setResolveForm((f) => ({ ...f, receiver_contact: e.target.value }))}
                      placeholder="Phone or email"
                      className="input-field"
                    />
                  </div>
                  <div className="flex gap-3">
                    <button type="submit" disabled={resolving}
                      className="flex-1 py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-semibold hover:bg-emerald-600 transition-colors disabled:opacity-60">
                      {resolving ? 'Saving…' : 'Confirm Return'}
                    </button>
                    <button type="button" onClick={() => setShowResolve(false)}
                      className="px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-50">
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Actions */}
          {user && (canEdit || isAdmin) && (
            <div className="card p-5 space-y-3">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Actions</h3>
              {canEdit && (
                <Link to={`/items/${id}/edit`}
                  className="flex items-center gap-2 w-full px-4 py-2.5 border border-gray-200 text-gray-600
                             rounded-xl text-sm font-semibold hover:border-brand hover:text-brand transition-colors">
                  <i className="fa-solid fa-pen text-xs" /> Edit Report
                </Link>
              )}
              {(isOwner || isAdmin) && (
                <button onClick={handleDelete}
                  className="flex items-center gap-2 w-full px-4 py-2.5 border border-red-200 text-red-600
                             rounded-xl text-sm font-semibold hover:bg-red-50 transition-colors">
                  <i className="fa-solid fa-trash text-xs" /> Delete Report
                </button>
              )}
            </div>
          )}

          {/* Audit log */}
          {item.logs?.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-3.5 border-b border-gray-100">
                <h3 className="text-xs font-bold text-gray-800">Activity Log</h3>
              </div>
              <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto">
                {item.logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-3 px-5 py-3">
                    <div className="w-6 h-6 rounded-full bg-brand/10 flex items-center justify-center shrink-0 mt-0.5">
                      <i className={`fa-solid ${log.action_icon} text-brand text-[9px]`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-700">{log.action_label}</p>
                      {log.note && <p className="text-[10px] text-gray-400 mt-0.5">{log.note}</p>}
                    </div>
                    <p className="text-[9px] text-gray-300 shrink-0 mt-0.5">
                      {new Date(log.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
