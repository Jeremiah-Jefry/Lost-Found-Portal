import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import api from '../api/axios'

const CATEGORIES = [
  { value: 'ELECTRONICS', label: 'Electronics & Gadgets' },
  { value: 'DOCUMENTS',   label: 'IDs & Documents' },
  { value: 'KEYS',        label: 'Keys & Access Cards' },
  { value: 'CLOTHING',    label: 'Clothing & Bags' },
  { value: 'OTHER',       label: 'Other' },
]

export default function ReportItem() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '', description: '', status: 'LOST', category: 'OTHER', location: '',
    handover_status: '', handover_details: '',
  })
  const [image, setImage]   = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors]  = useState({})

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleImage = (e) => {
    const file = e.target.files[0]
    setImage(file || null)
    setPreview(file ? URL.createObjectURL(file) : null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); setErrors({}); setLoading(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => { if (v) fd.append(k, v) })
      if (image) fd.append('image', image)
      const { data } = await api.post('/items/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      navigate(`/items/${data.id}`)
    } catch (err) {
      setErrors(err.response?.data || { detail: 'Failed to submit report.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout title="Report Item">
      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Status toggle */}
          <div className="card p-5">
            <label className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-3">Report Type</label>
            <div className="flex gap-3">
              {[['LOST', 'I lost something', 'fa-circle-exclamation', 'red'], ['FOUND', 'I found something', 'fa-circle-check', 'emerald']].map(([val, lbl, icon, color]) => (
                <button
                  key={val} type="button"
                  onClick={() => setForm((f) => ({ ...f, status: val }))}
                  className={`flex-1 flex items-center gap-2.5 px-4 py-3 rounded-xl border-2 text-sm font-semibold transition-all ${
                    form.status === val
                      ? `border-${color}-400 bg-${color}-50 text-${color}-700`
                      : 'border-gray-200 text-gray-500 hover:border-gray-300'
                  }`}
                >
                  <i className={`fa-solid ${icon}`} /> {lbl}
                </button>
              ))}
            </div>
          </div>

          {/* Details */}
          <div className="card p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-800">Item Details</h3>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">Item Name *</label>
              <input name="title" value={form.title} onChange={handleChange} required maxLength={200}
                placeholder="e.g. Blue backpack, iPhone 14, Student ID"
                className="input-field" />
              {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">Description *</label>
              <textarea name="description" value={form.description} onChange={handleChange} required maxLength={2000}
                rows={4} placeholder="Describe the item in detail — colour, brand, distinguishing features…"
                className="input-field resize-none" />
              {errors.description && <p className="text-xs text-red-500 mt-1">{errors.description}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Category *</label>
                <select name="category" value={form.category} onChange={handleChange} className="input-field">
                  {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Location *</label>
                <input name="location" value={form.location} onChange={handleChange} required maxLength={255}
                  placeholder="e.g. Library 2nd floor, Block A canteen"
                  className="input-field" />
                {errors.location && <p className="text-xs text-red-500 mt-1">{errors.location}</p>}
              </div>
            </div>
          </div>

          {/* Image upload */}
          <div className="card p-6">
            <h3 className="text-sm font-bold text-gray-800 mb-4">Photo (optional)</h3>
            <label className="flex flex-col items-center gap-3 border-2 border-dashed border-gray-200 rounded-xl p-6 cursor-pointer hover:border-brand hover:bg-brand-xlight transition-all group">
              {preview ? (
                <img src={preview} alt="Preview" className="max-h-40 rounded-lg object-contain" />
              ) : (
                <>
                  <i className="fa-solid fa-cloud-arrow-up text-3xl text-gray-300 group-hover:text-brand transition-colors" />
                  <p className="text-xs text-gray-400 group-hover:text-brand transition-colors">Click to upload — PNG, JPG, GIF, WEBP · Max 2 MB</p>
                </>
              )}
              <input type="file" accept="image/*" onChange={handleImage} className="hidden" />
            </label>
          </div>

          {/* Handover (FOUND items) */}
          {form.status === 'FOUND' && (
            <div className="card p-6 space-y-4">
              <h3 className="text-sm font-bold text-gray-800">Item Custody</h3>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Where is the item now?</label>
                <select name="handover_status" value={form.handover_status} onChange={handleChange} className="input-field">
                  <option value="">— Select —</option>
                  <option value="LEFT_AT_LOCATION">Left at Location</option>
                  <option value="WITH_FINDER">With Me (Finder)</option>
                  <option value="SECURITY">Handed to Security</option>
                </select>
              </div>
              {form.handover_status && (
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1.5">Details</label>
                  <textarea name="handover_details" value={form.handover_details} onChange={handleChange}
                    rows={2} placeholder="Any additional custody information…"
                    className="input-field resize-none" />
                </div>
              )}
            </div>
          )}

          {errors.detail && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">{errors.detail}</p>
          )}

          <div className="flex gap-3 pb-8">
            <button type="submit" disabled={loading}
              className="flex-1 btn-primary disabled:opacity-60">
              {loading ? <><i className="fa-solid fa-circle-notch fa-spin" /> Submitting…</> : <><i className="fa-solid fa-paper-plane" /> Submit Report</>}
            </button>
            <button type="button" onClick={() => navigate(-1)}
              className="px-5 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </Layout>
  )
}
