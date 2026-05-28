import { useState } from 'react'
import type { Court, CourtCreate } from '../api/client'

interface CourtFormProps {
  court?: Court
  onSubmit: (data: CourtCreate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

const COURT_TYPES = ['state', 'federal', 'bankruptcy', 'appellate', 'other']
const CATEGORIES = ['civil', 'criminal', 'family', 'probate', 'all']

export default function CourtForm({
  court,
  onSubmit,
  onCancel,
  isLoading,
}: CourtFormProps) {
  const [form, setForm] = useState<CourtCreate>({
    name: court?.name || '',
    url: court?.url || '',
    court_type: court?.court_type || 'other',
    state: court?.state || '',
    category: court?.category || 'all',
    active: court?.active ?? true,
    js_required: court?.js_required ?? false,
    css_selector: court?.css_selector || '',
    notes: court?.notes || '',
  })
  const [error, setError] = useState<string | null>(null)

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!form.name.trim()) {
      setError('Name is required')
      return
    }
    if (!form.url.trim() || !form.url.startsWith('http')) {
      setError('A valid URL starting with http:// or https:// is required')
      return
    }
    try {
      await onSubmit({
        ...form,
        state: form.state?.trim() || null,
        css_selector: form.css_selector?.trim() || null,
        notes: form.notes?.trim() || null,
      })
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to save court')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded p-3">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Court Name *
          </label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            URL *
          </label>
          <input
            type="url"
            name="url"
            value={form.url}
            onChange={handleChange}
            required
            placeholder="https://..."
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Court Type
          </label>
          <select
            name="court_type"
            value={form.court_type}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {COURT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            State (2-letter)
          </label>
          <input
            type="text"
            name="state"
            value={form.state || ''}
            onChange={handleChange}
            maxLength={2}
            placeholder="TX"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            name="category"
            value={form.category}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            CSS Selector (optional)
          </label>
          <input
            type="text"
            name="css_selector"
            value={form.css_selector || ''}
            onChange={handleChange}
            placeholder="#main-content"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex gap-6">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            name="active"
            checked={form.active}
            onChange={handleChange}
            className="rounded border-gray-300"
          />
          Active
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            name="js_required"
            checked={form.js_required}
            onChange={handleChange}
            className="rounded border-gray-300"
          />
          Requires JavaScript (Playwright)
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          name="notes"
          value={form.notes || ''}
          onChange={handleChange}
          rows={3}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : court ? 'Update Court' : 'Add Court'}
        </button>
      </div>
    </form>
  )
}
