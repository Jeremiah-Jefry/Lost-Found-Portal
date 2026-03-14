import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
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

export default function AdminAnalytics() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/analytics/').then((r) => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <Layout title="Analytics">
      <div className="flex justify-center py-20"><i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" /></div>
    </Layout>
  )

  const ov = data?.overview || {}
  const mt = data?.metrics  || {}
  const hv = data?.handover || {}
  const us = data?.users    || {}

  const handoverTotal = (hv.security || 0) + (hv.with_finder || 0) + (hv.left || 0)
  const pct = (n) => handoverTotal > 0 ? Math.round(n / handoverTotal * 100) : 0

  return (
    <Layout title="Analytics">
      {/* Admin badge */}
      <div className="flex items-center gap-2 mb-6">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-violet-50 text-violet-700 border border-violet-200 rounded-full text-xs font-bold uppercase tracking-wider">
          <i className="fa-solid fa-shield-halved text-xs" /> Administrator View
        </span>
        <span className="text-xs text-gray-400">{new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
      </div>

      {/* Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon="fa-solid fa-layer-group"        iconBg="bg-blue-50"    iconColor="text-brand"       label="Total"    value={ov.total_items    ?? 0} sub="Reports all-time" />
        <StatCard icon="fa-solid fa-circle-exclamation" iconBg="bg-red-50"     iconColor="text-red-500"     label="Lost"     value={ov.total_lost     ?? 0} sub="Open lost reports" />
        <StatCard icon="fa-solid fa-circle-check"       iconBg="bg-emerald-50" iconColor="text-emerald-500" label="Found"    value={ov.total_found    ?? 0} sub="Found reports" />
        <StatCard icon="fa-solid fa-check-double"       iconBg="bg-violet-50"  iconColor="text-violet-600"  label="Returned" value={ov.total_returned ?? 0} sub="Cases closed" />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {/* Same-day rate */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center">
              <i className="fa-solid fa-bolt text-amber-500 text-sm" />
            </div>
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Same-Day Retrieval</p>
              <p className="text-[10px] text-gray-300 mt-0.5">Items returned on reporting day</p>
            </div>
          </div>
          <p className="text-4xl font-extrabold text-gray-900">
            {mt.same_day_rate}<span className="text-xl text-gray-400 font-semibold">%</span>
          </p>
          <p className="text-xs text-gray-400 mt-1">{mt.same_day_count} of {mt.total_resolved} resolved items</p>
          <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-amber-400 rounded-full" style={{ width: `${mt.same_day_rate}%` }} />
          </div>
        </div>

        {/* Case status */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <i className="fa-solid fa-chart-pie text-brand text-sm" />
            </div>
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Case Status</p>
              <p className="text-[10px] text-gray-300 mt-0.5">Current lifecycle breakdown</p>
            </div>
          </div>
          <div className="space-y-2.5">
            {[
              { label: 'Open',     val: ov.total_open,     dot: 'bg-blue-400' },
              { label: 'Secured',  val: ov.total_secured,  dot: 'bg-amber-400' },
              { label: 'Returned', val: ov.total_returned, dot: 'bg-emerald-500' },
            ].map(({ label, val, dot }) => (
              <div key={label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${dot}`} />
                  <span className="text-xs text-gray-600 font-medium">{label}</span>
                </div>
                <span className="text-sm font-bold text-gray-800">{val ?? 0}</span>
              </div>
            ))}
          </div>
        </div>

        {/* User roster summary */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center">
              <i className="fa-solid fa-users text-violet-500 text-sm" />
            </div>
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Users</p>
              <p className="text-[10px] text-gray-300 mt-0.5">Registered portal accounts</p>
            </div>
          </div>
          <div className="space-y-2.5">
            {[
              { label: 'Students',    val: us.total_users, dot: 'bg-gray-300' },
              { label: 'Staff/Admin', val: us.total_staff, dot: 'bg-brand' },
            ].map(({ label, val, dot }) => (
              <div key={label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${dot}`} />
                  <span className="text-xs text-gray-600 font-medium">{label}</span>
                </div>
                <span className="text-sm font-bold text-gray-800">{val ?? 0}</span>
              </div>
            ))}
            <div className="flex items-center justify-between border-t border-gray-100 pt-2.5">
              <span className="text-xs text-gray-500 font-semibold">Total</span>
              <span className="text-sm font-bold text-gray-800">{(us.total_users || 0) + (us.total_staff || 0)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Activity + Handover */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Daily activity */}
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
            <i className="fa-solid fa-calendar-days text-brand text-sm" />
            <h3 className="text-sm font-bold text-gray-800">Daily Activity — Last 7 Days</h3>
          </div>
          <div className="p-5 space-y-3">
            {(() => {
              const activity = data?.daily_activity || []
              const maxVal = Math.max(1, ...activity.map((d) => (d.lost || 0) + (d.found || 0)))
              return activity.map((day) => {
                const total = (day.lost || 0) + (day.found || 0)
                return (
                  <div key={day.date} className="flex items-center gap-3">
                    <p className="text-xs font-semibold text-gray-400 w-14 shrink-0">{day.date}</p>
                    <div className="flex-1 flex gap-1 h-5">
                      {day.lost  > 0 && <div className="bg-red-400 rounded-sm"    style={{ width: `${Math.round(day.lost  / maxVal * 100)}%`, minWidth: 4 }} />}
                      {day.found > 0 && <div className="bg-emerald-400 rounded-sm" style={{ width: `${Math.round(day.found / maxVal * 100)}%`, minWidth: 4 }} />}
                      {total === 0 && <div className="bg-gray-100 rounded-sm flex-1" />}
                    </div>
                    <p className="text-xs font-bold text-gray-500 w-6 text-right shrink-0">{total}</p>
                  </div>
                )
              })
            })()}
            <div className="flex items-center gap-4 pt-2 border-t border-gray-100">
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-red-400" /><span className="text-[10px] text-gray-400 font-semibold">Lost</span></div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-emerald-400" /><span className="text-[10px] text-gray-400 font-semibold">Found</span></div>
            </div>
          </div>
        </div>

        {/* Handover stats */}
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
            <i className="fa-solid fa-hand-holding text-amber-500 text-sm" />
            <h3 className="text-sm font-bold text-gray-800">Handover Statistics</h3>
          </div>
          <div className="p-5 space-y-4">
            {[
              { label: 'Handed to Security', val: hv.security,    icon: 'fa-shield-halved', bg: 'bg-amber-50', border: 'border-amber-100', iconBg: 'bg-amber-100', iconColor: 'text-amber-600', barBg: 'bg-amber-200', barFill: 'bg-amber-500', textColor: 'text-amber-700' },
              { label: 'With Finder',         val: hv.with_finder, icon: 'fa-user',          bg: 'bg-blue-50',  border: 'border-blue-100',  iconBg: 'bg-blue-100',  iconColor: 'text-brand',    barBg: 'bg-blue-200',  barFill: 'bg-brand',    textColor: 'text-brand' },
              { label: 'Left at Location',    val: hv.left,        icon: 'fa-map-pin',       bg: 'bg-gray-50',  border: 'border-gray-100',  iconBg: 'bg-gray-100',  iconColor: 'text-gray-500', barBg: 'bg-gray-200',  barFill: 'bg-gray-400', textColor: 'text-gray-600' },
            ].map(({ label, val, icon, bg, border, iconBg, iconColor, barBg, barFill, textColor }) => (
              <div key={label} className={`flex items-center gap-4 p-4 ${bg} rounded-xl border ${border}`}>
                <div className={`w-10 h-10 rounded-xl ${iconBg} flex items-center justify-center shrink-0`}>
                  <i className={`fa-solid ${icon} ${iconColor} text-sm`} />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-bold text-gray-700">{label}</p>
                  <div className={`mt-1.5 h-1 ${barBg} rounded-full overflow-hidden`}>
                    <div className={`h-full ${barFill} rounded-full`} style={{ width: `${pct(val || 0)}%` }} />
                  </div>
                </div>
                <span className={`text-xl font-extrabold ${textColor}`}>{val ?? 0}</span>
              </div>
            ))}
            {handoverTotal === 0 && <p className="text-sm text-center text-gray-400 py-2">No handover data yet.</p>}
          </div>
        </div>
      </div>

      {/* Staff Roster */}
      <div className="card overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <i className="fa-solid fa-id-badge text-brand text-sm" />
            <h3 className="text-sm font-bold text-gray-800">Staff & Admin Roster</h3>
          </div>
          <span className="text-xs font-bold text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200">
            {us.staff_roster?.length || 0} account{us.staff_roster?.length !== 1 ? 's' : ''}
          </span>
        </div>
        {us.staff_roster?.length > 0 ? (
          <div className="divide-y divide-gray-50">
            {us.staff_roster.map((u) => (
              <div key={u.id} className="flex items-center gap-4 px-6 py-3.5">
                <div className="w-9 h-9 rounded-full bg-brand text-white flex items-center justify-center font-bold text-sm shadow-sm shrink-0">
                  {u.username[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-800">{u.username}</p>
                  <p className="text-xs text-gray-400 truncate">{u.email}</p>
                </div>
                <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                  u.role === 'ADMIN'
                    ? 'bg-violet-50 text-violet-700 border border-violet-200'
                    : 'bg-blue-50 text-blue-700 border border-blue-200'
                }`}>
                  {u.role === 'ADMIN' && <i className="fa-solid fa-crown text-[9px] mr-0.5" />}
                  {u.role_label}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-10 text-center">
            <i className="fa-solid fa-users text-3xl text-gray-200 mb-3 block" />
            <p className="text-sm text-gray-400">No staff accounts yet.</p>
          </div>
        )}
      </div>

      {/* Audit Log */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
          <i className="fa-solid fa-clock-rotate-left text-brand text-sm" />
          <h3 className="text-sm font-bold text-gray-800">Recent Audit Activity</h3>
          <span className="ml-auto text-xs text-gray-400">Last 25 events</span>
        </div>
        {data?.recent_logs?.length > 0 ? (
          <div className="divide-y divide-gray-50">
            {data.recent_logs.map((log) => (
              <div key={log.id} className="flex items-start gap-4 px-6 py-3.5">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  log.action === 'CREATED' ? 'bg-brand' :
                  log.action === 'RESOLVED' ? 'bg-emerald-500' :
                  log.action === 'MATCH_FOUND' ? 'bg-amber-500' :
                  log.action === 'STATUS_CHANGED' ? 'bg-violet-500' : 'bg-gray-300'
                }`}>
                  <i className={`fa-solid ${log.action_icon} text-white text-[9px]`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-800">{log.action_label}</p>
                  {log.note && <p className="text-xs text-gray-400 mt-0.5 truncate">{log.note}</p>}
                  {log.from_value && log.to_value && (
                    <div className="flex items-center gap-1 mt-1">
                      <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded font-mono">{log.from_value}</span>
                      <i className="fa-solid fa-arrow-right text-gray-300 text-[9px]" />
                      <span className="text-[10px] px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded font-mono">{log.to_value}</span>
                    </div>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <p className="text-[10px] font-semibold text-gray-500">{log.actor?.username || 'System'}</p>
                  {log.actor?.role_label && <p className="text-[9px] text-brand font-bold uppercase tracking-wider">{log.actor.role_label}</p>}
                  <p className="text-[10px] text-gray-300 mt-0.5">
                    {new Date(log.created_at).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-10 text-center">
            <i className="fa-solid fa-scroll text-3xl text-gray-200 mb-3 block" />
            <p className="text-sm text-gray-400">No audit events yet.</p>
          </div>
        )}
      </div>
    </Layout>
  )
}
