import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

const CATEGORIES = [
  { value: 'ELECTRONICS', label: 'Electronics & Gadgets' },
  { value: 'DOCUMENTS',   label: 'IDs & Documents' },
  { value: 'KEYS',        label: 'Keys & Access Cards' },
  { value: 'CLOTHING',    label: 'Clothing & Bags' },
  { value: 'OTHER',       label: 'Other' },
]

export default function EditItem() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [form, setForm]     = useState(null)
  const [image, setImage]   = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    api.get(`/items/${id}/`).then((r) => {
      const d = r.data
      setForm({
        title: d.title, description: d.description, status: d.status,
        category: d.category, location: d.location,
        handover_status: d.handover_status || '',
        handover_details: d.handover_details || '',
      })
      setPreview(d.image_url || null)
    }).catch(() => navigate('/feed')).finally(() => setLoading(false))
  }, [id, navigate])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleImage = (e) => {
    const file = e.target.files[0]
    setImage(file || null)
    setPreview(file ? URL.createObjectURL(file) : null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); setErrors({}); setSubmitting(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => { if (v !== null && v !== undefined) fd.append(k, v) })
      if (image) fd.append('image', image)
      await api.patch(`/items/${id}/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      navigate(`/items/${id}`)
    } catch (err) {
      setErrors(err.response?.data || { detail: 'Failed to update report.' })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || !form) return (
    <Layout title="Edit Report">
      <div className="flex justify-center py-20"><i className="fa-solid fa-circle-notch fa-spin text-brand text-3xl" /></div>
    </Layout>
  )

  return (
    <Layout title="Edit Report">
      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="card p-5">
            <label className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-3">Report Type</label>
            <div className="flex gap-3">
              {[['LOST', 'Lost Item', 'fa-circle-exclamation'], ['FOUND', 'Found Item', 'fa-circle-check']].map(([val, lbl, icon]) => (
                <button key={val} type="button"
                  onClick={() => setForm((f) => ({ ...f, status: val }))}
                  className={`flex-1 flex items-center gap-2.5 px-4 py-3 rounded-xl border-2 text-sm font-semibold transition-all ${
                    form.status === val ? 'border-brand bg-brand-xlight text-brand' : 'border-gray-200 text-gray-500'
                  }`}
                >
                  <i className={`fa-solid ${icon}`} /> {lbl}
                </button>
              ))}
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">Item Name *</label>
              <input name="title" value={form.title} onChange={handleChange} required maxLength={200} className="input-field" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">Description *</label>
              <textarea name="description" value={form.description} onChange={handleChange} required rows={4} className="input-field resize-none" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Category</label>
                <select name="category" value={form.category} onChange={handleChange} className="input-field">
                  {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Location *</label>
                <input name="location" value={form.location} onChange={handleChange} required maxLength={255} className="input-field" />
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-sm font-bold text-gray-800 mb-4">Photo</h3>
            <label className="flex flex-col items-center gap-3 border-2 border-dashed border-gray-200 rounded-xl p-6 cursor-pointer hover:border-brand hover:bg-brand-xlight transition-all group">
              {preview ? <img src={preview} alt="Preview" className="max-h-40 rounded-lg object-contain" /> : (
                <><i className="fa-solid fa-cloud-arrow-up text-3xl text-gray-300 group-hover:text-brand" />
                <p className="text-xs text-gray-400">Click to change photo</p></>
              )}
              <input type="file" accept="image/*" onChange={handleImage} className="hidden" />
            </label>
          </div>

          {errors.detail && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">{errors.detail}</p>
          )}

          <div className="flex gap-3 pb-8">
            <button type="submit" disabled={submitting} className="flex-1 btn-primary disabled:opacity-60">
              {submitting ? 'Saving…' : <><i className="fa-solid fa-floppy-disk" /> Save Changes</>}
            </button>
            <button type="button" onClick={() => navigate(`/items/${id}`)}
              className="px-5 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </Layout>
  )
}
