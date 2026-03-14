import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import ItemCard from '../components/ItemCard'
import api from '../api/axios'

function StatCard({ icon, iconBg, iconColor, label, value, sub }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-9 h-9 rounded-xl ${iconBg} flex items-center justify-center`}>
          <i className={`${icon} ${iconColor} text-sm`} />
        </div>
        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{label}</span>
      </div>
      <p className={`text-3xl font-extrabold ${iconColor}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/dashboard/').then((r) => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <Layout title="Dashboard">
      <div className="flex justify-center py-20">
        <i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" />
      </div>
    </Layout>
  )

  const c = data?.counts || {}

  return (
    <Layout title="Dashboard">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon="fa-solid fa-circle-exclamation" iconBg="bg-red-50"     iconColor="text-red-500"    label="Open Lost"  value={c.open_lost  ?? 0} sub="Active lost reports" />
        <StatCard icon="fa-solid fa-circle-check"       iconBg="bg-emerald-50" iconColor="text-emerald-500" label="Open Found" value={c.open_found ?? 0} sub="Found, awaiting claim" />
        <StatCard icon="fa-solid fa-shield-halved"      iconBg="bg-amber-50"   iconColor="text-amber-500"  label="Secured"    value={c.secured    ?? 0} sub="At security office" />
        <StatCard icon="fa-solid fa-check-double"       iconBg="bg-violet-50"  iconColor="text-violet-600" label="Returned"   value={c.returned   ?? 0} sub="Cases closed" />
      </div>

      {/* Unreviewed matches banner */}
      {c.unreviewed_matches > 0 && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-center gap-3">
          <i className="fa-solid fa-link text-amber-500 text-lg shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-800">
              {c.unreviewed_matches} potential match{c.unreviewed_matches !== 1 ? 'es' : ''} pending review
            </p>
            <p className="text-xs text-amber-600 mt-0.5">Auto-match engine found likely item pairs</p>
          </div>
        </div>
      )}

      {/* Dual-stream layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lost column */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-400" />
              <h2 className="text-sm font-bold text-gray-800">Recent Lost Reports</h2>
            </div>
            <Link to="/feed?status=LOST" className="text-xs text-brand hover:underline font-medium">View all →</Link>
          </div>
          {data?.recent_lost?.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">No open lost reports.</p>
          )}
          <div className="space-y-3">
            {data?.recent_lost?.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>

        {/* Found column */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <h2 className="text-sm font-bold text-gray-800">Recent Found Reports</h2>
            </div>
            <Link to="/feed?status=FOUND" className="text-xs text-brand hover:underline font-medium">View all →</Link>
          </div>
          {data?.recent_found?.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">No open found reports.</p>
          )}
          <div className="space-y-3">
            {data?.recent_found?.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
