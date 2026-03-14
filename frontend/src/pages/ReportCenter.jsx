import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import ItemCard from '../components/ItemCard'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

export default function ReportCenter() {
  const { user } = useAuth()
  const [items, setItems]     = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/items/mine/').then((r) => setItems(r.data.results || r.data)).finally(() => setLoading(false))
  }, [])

  const open     = items.filter((i) => i.resolution_status !== 'RETURNED')
  const resolved = items.filter((i) => i.resolution_status === 'RETURNED')

  return (
    <Layout title="My Reports">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-extrabold text-gray-900">
            Welcome back, <span className="text-brand">{user?.username}</span>
          </h2>
          <p className="text-sm text-gray-400 mt-0.5">Track and manage your lost & found reports</p>
        </div>
        <Link to="/report" className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand text-white
               rounded-xl text-sm font-semibold hover:bg-brand-dark transition-colors shadow-md shadow-blue-200/60">
          <i className="fa-solid fa-plus" /> Report Item
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" />
        </div>
      ) : items.length === 0 ? (
        <div className="card p-16 text-center">
          <i className="fa-solid fa-inbox text-4xl text-gray-200 mb-4 block" />
          <p className="text-sm font-semibold text-gray-500">No reports yet</p>
          <p className="text-xs text-gray-400 mt-1">Click "Report Item" to submit your first report.</p>
        </div>
      ) : (
        <>
          {open.length > 0 && (
            <section className="mb-8">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
                Active ({open.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {open.map((item) => <ItemCard key={item.id} item={item} />)}
              </div>
            </section>
          )}
          {resolved.length > 0 && (
            <section>
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
                Resolved ({resolved.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 opacity-60">
                {resolved.map((item) => <ItemCard key={item.id} item={item} />)}
              </div>
            </section>
          )}
        </>
      )}
    </Layout>
  )
}
