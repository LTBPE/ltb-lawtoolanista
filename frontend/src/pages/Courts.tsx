import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCourts,
  createCourt,
  updateCourt,
  deleteCourt,
  triggerScan,
} from '../api/client'
import type { Court, CourtCreate } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import CourtForm from './CourtForm'

function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black bg-opacity-40 overflow-y-auto pt-10 pb-10">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            x
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  )
}

export default function Courts() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(true)
  const [editCourt, setEditCourt] = useState<Court | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [scanningId, setScanningId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['courts', page, stateFilter, typeFilter, activeFilter],
    queryFn: () =>
      getCourts({
        page,
        page_size: 25,
        state: stateFilter || undefined,
        court_type: typeFilter || undefined,
        active: activeFilter,
      }),
  })

  const createMutation = useMutation({
    mutationFn: createCourt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courts'] })
      setShowAddForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CourtCreate> }) =>
      updateCourt(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courts'] })
      setEditCourt(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCourt,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courts'] }),
  })

  const handleScan = async (id: number) => {
    setScanningId(id)
    try {
      await triggerScan(id)
    } finally {
      setScanningId(null)
    }
  }

  const handleDisable = async (court: Court) => {
    if (window.confirm(`Disable monitoring for "${court.name}"?`)) {
      await deleteMutation.mutateAsync(court.id)
    }
  }

  const filteredItems = (data?.items || []).filter((c) =>
    search
      ? c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.url.toLowerCase().includes(search.toLowerCase())
      : true
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-2xl font-bold text-gray-900">Courts</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          + Add Court
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          placeholder="Search name or URL..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="State (TX)"
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value.toUpperCase())}
          maxLength={2}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm w-24 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Types</option>
          {['state', 'federal', 'bankruptcy', 'appellate', 'other'].map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={activeFilter === undefined ? '' : activeFilter ? 'true' : 'false'}
          onChange={(e) =>
            setActiveFilter(
              e.target.value === '' ? undefined : e.target.value === 'true'
            )
          }
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="true">Active Only</option>
          <option value="false">Inactive Only</option>
          <option value="">All</option>
        </select>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">State</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Last Scanned</th>
                <th className="px-4 py-3">Last Changed</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-gray-400">
                    Loading...
                  </td>
                </tr>
              )}
              {!isLoading && filteredItems.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-gray-400">
                    No courts found
                  </td>
                </tr>
              )}
              {filteredItems.map((court) => (
                <tr key={court.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium">{court.name}</div>
                    <div className="text-xs text-gray-400 truncate max-w-xs">
                      <a
                        href={court.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-blue-500"
                      >
                        {court.url}
                      </a>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{court.state || '-'}</td>
                  <td className="px-4 py-3 text-gray-600">{court.court_type}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {court.last_scanned_at
                      ? new Date(court.last_scanned_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {court.last_changed_at
                      ? new Date(court.last_changed_at).toLocaleDateString()
                      : '-'}
                  </td>
                  <td className="px-4 py-3">
                    {court.consecutive_errors > 0 ? (
                      <StatusBadge status="error" />
                    ) : court.active ? (
                      <StatusBadge status="success" />
                    ) : (
                      <StatusBadge status="skipped" />
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEditCourt(court)}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleScan(court.id)}
                        disabled={scanningId === court.id}
                        className="text-xs text-green-600 hover:underline disabled:opacity-50"
                      >
                        {scanningId === court.id ? 'Queued' : 'Scan Now'}
                      </button>
                      {court.active && (
                        <button
                          onClick={() => handleDisable(court)}
                          className="text-xs text-red-500 hover:underline"
                        >
                          Disable
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total > 25 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
            <span>
              {(page - 1) * 25 + 1} - {Math.min(page * 25, data.total)} of{' '}
              {data.total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * 25 >= data.total}
                className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Court Modal */}
      {showAddForm && (
        <Modal title="Add Court" onClose={() => setShowAddForm(false)}>
          <CourtForm
            onSubmit={(data) => createMutation.mutateAsync(data)}
            onCancel={() => setShowAddForm(false)}
            isLoading={createMutation.isPending}
          />
        </Modal>
      )}

      {/* Edit Court Modal */}
      {editCourt && (
        <Modal title="Edit Court" onClose={() => setEditCourt(null)}>
          <CourtForm
            court={editCourt}
            onSubmit={(data) =>
              updateMutation.mutateAsync({ id: editCourt.id, data })
            }
            onCancel={() => setEditCourt(null)}
            isLoading={updateMutation.isPending}
          />
        </Modal>
      )}
    </div>
  )
}
