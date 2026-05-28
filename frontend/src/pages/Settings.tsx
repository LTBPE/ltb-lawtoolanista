import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAlertConfig, updateAlertConfig } from '../api/client'
import type { AlertConfig } from '../api/client'

export default function Settings() {
  const queryClient = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [form, setForm] = useState<Partial<AlertConfig>>({})

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: getAlertConfig,
  })

  useEffect(() => {
    if (config) {
      setForm({
        email_recipients: config.email_recipients,
        notify_immediately: config.notify_immediately,
        notify_digest_time: config.notify_digest_time || '',
        min_priority: config.min_priority,
        ai_filter_enabled: config.ai_filter_enabled,
      })
    }
  }, [config])

  const updateMutation = useMutation({
    mutationFn: updateAlertConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate({
      ...form,
      notify_digest_time: form.notify_digest_time || null,
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400">
        Loading...
      </div>
    )
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Alert Email Recipients
          </label>
          <input
            type="text"
            name="email_recipients"
            value={form.email_recipients || ''}
            onChange={handleChange}
            placeholder="user@lawtoolbox.com, other@lawtoolbox.com"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">
            Comma-separated list of email addresses
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Notification Mode
          </label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                name="notify_immediately"
                checked={form.notify_immediately ?? true}
                onChange={handleChange}
                className="rounded border-gray-300"
              />
              Send immediate email alerts for new relevant changes
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Daily Digest Time (optional)
          </label>
          <input
            type="time"
            name="notify_digest_time"
            value={form.notify_digest_time || ''}
            onChange={handleChange}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">
            If set, a daily digest will be sent at this time (UTC)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Priority for Alerts
          </label>
          <select
            name="min_priority"
            value={form.min_priority || 'low'}
            onChange={handleChange}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="low">Low (all changes)</option>
            <option value="medium">Medium and above</option>
            <option value="high">High only</option>
          </select>
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              name="ai_filter_enabled"
              checked={form.ai_filter_enabled ?? true}
              onChange={handleChange}
              className="rounded border-gray-300"
            />
            Enable AI relevance filtering
          </label>
          <p className="text-xs text-gray-400 mt-1">
            When enabled, Claude AI analyzes each change and skips notifications
            for changes unrelated to docketing rules. Disable to receive all
            change notifications.
          </p>
        </div>

        <div className="flex items-center gap-4 pt-2">
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="px-5 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
          </button>
          {saved && (
            <span className="text-sm text-green-600 font-medium">
              Settings saved
            </span>
          )}
          {updateMutation.isError && (
            <span className="text-sm text-red-600">Failed to save</span>
          )}
        </div>
      </form>
    </div>
  )
}
