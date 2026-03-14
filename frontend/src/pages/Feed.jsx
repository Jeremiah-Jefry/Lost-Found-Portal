import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import ItemCard from '../components/ItemCard'
import api from '../api/axios'

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'ELECTRONICS', label: 'Electronics & Gadgets' },
  { value: 'DOCUMENTS',   label: 'IDs & Documents' },
  { value: 'KEYS',        label: 'Keys & Access Cards' },
  { value: 'CLOTHING',    label: 'Clothing & Bags' },
  { value: 'OTHER',       label: 'Other' },
]

export default function Feed() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [items, setItems]     = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage]       = useState(1)
  const [hasNext, setHasNext] = useState(false)

  const q        = searchParams.get('q') || ''
  const status   = searchParams.get('status') || ''
  const category = searchParams.get('category') || ''

  const fetchItems = useCallback(async (pg = 1) => {
    setLoading(true)
    try {
      const params = { page: pg }
      if (q)        params.search   = q
      if (status)   params.status   = status
      if (category) params.category = category
      const { data } = await api.get('/items/', { params })
      const results = data.results || data
      setItems(pg === 1 ? results : (prev) => [...prev, ...results])
      setHasNext(!!data.next)
      setPage(pg)
    } finally {
      setLoading(false)
    }
  }, [q, status, category])

  useEffect(() => { fetchItems(1) }, [fetchItems])

  const setParam = (key, val) => {
    const next = new URLSearchParams(searchParams)
    if (val) next.set(key, val); else next.delete(key)
    setSearchParams(next)
  }

  return (
    <Layout title="Item Feed">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex gap-1.5">
          {[['', 'All'], ['LOST', 'Lost'], ['FOUND', 'Found']].map(([v, l]) => (
            <button
              key={v}
              onClick={() => setParam('status', v)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                status === v
                  ? 'bg-brand text-white border-brand'
                  : 'bg-white text-gray-500 border-gray-200 hover:border-brand hover:text-brand'
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        <select
          value={category}
          onChange={(e) => setParam('category', e.target.value)}
          className="input-field !w-auto text-xs"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>

        {(q || status || category) && (
          <button
            onClick={() => setSearchParams({})}
            className="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1 transition-colors"
          >
            <i className="fa-solid fa-xmark" /> Clear filters
          </button>
        )}
      </div>

      {/* Results */}
      {loading && page === 1 ? (
        <div className="flex justify-center py-20">
          <i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" />
        </div>
      ) : items.length === 0 ? (
        <div className="card p-16 text-center">
          <i className="fa-solid fa-magnifying-glass text-4xl text-gray-200 mb-4 block" />
          <p className="text-sm font-semibold text-gray-500">No items found</p>
          <p className="text-xs text-gray-400 mt-1">Try adjusting your search or filters.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {items.map((item) => <ItemCard key={item.id} item={item} />)}
          </div>
          {hasNext && (
            <div className="mt-8 text-center">
              <button
                onClick={() => fetchItems(page + 1)}
                disabled={loading}
                className="px-6 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-semibold
                           text-gray-600 hover:border-brand hover:text-brand transition-colors disabled:opacity-60"
              >
                {loading ? <i className="fa-solid fa-circle-notch fa-spin" /> : 'Load more'}
              </button>
            </div>
          )}
        </>
      )}
    </Layout>
  )
}
