import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getChanges, updateChangeStatus } from '../api/client'
import type { Change } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import DiffViewer from '../components/DiffViewer'

export default function Changes() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['changes', page, statusFilter, priorityFilter],
    queryFn: () =>
      getChanges({
        page,
        page_size: 25,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateChangeStatus(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['changes'] }),
  })

  const handleStatusChange = async (change: Change, newStatus: string) => {
    await updateMutation.mutateAsync({ id: change.id, status: newStatus })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-2xl font-bold text-gray-900">Changes</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(1)
          }}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="in_review">In Review</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => {
            setPriorityFilter(e.target.value)
            setPage(1)
          }}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Court</th>
                <th className="px-4 py-3">Detected</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Summary</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-6 text-center text-gray-400"
                  >
                    Loading...
                  </td>
                </tr>
              )}
              {!isLoading && (data?.items || []).length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-6 text-center text-gray-400"
                  >
                    No changes found
                  </td>
                </tr>
              )}
              {(data?.items || []).map((change) => (
                <>
                  <tr
                    key={change.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() =>
                      setExpandedId(
                        expandedId === change.id ? null : change.id
                      )
                    }
                  >
                    <td className="px-4 py-3">
                      {change.ai_priority ? (
                        <StatusBadge
                          status={change.ai_priority}
                          type="priority"
                        />
                      ) : (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">
                        {change.court_name || `Court ${change.court_id}`}
                      </div>
                      {change.court_url && (
                        <div className="text-xs text-gray-400 truncate max-w-xs">
                          {change.court_url}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                      {new Date(change.detected_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {change.ai_category || '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 max-w-xs">
                      <div className="truncate">
                        {change.ai_summary || 'No summary'}
                      </div>
                    </td>
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <select
                        value={change.status}
                        onChange={(e) =>
                          handleStatusChange(change, e.target.value)
                        }
                        className="border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="new">New</option>
                        <option value="in_review">In Review</option>
                        <option value="resolved">Resolved</option>
                        <option value="false_positive">False Positive</option>
                      </select>
                    </td>
                  </tr>

                  {expandedId === change.id && (
                    <tr key={`${change.id}-expanded`}>
                      <td colSpan={6} className="px-4 py-4 bg-gray-50 border-t">
                        <div className="space-y-3">
                          {change.ai_action && (
                            <div className="bg-amber-50 border border-amber-200 rounded p-3">
                              <span className="font-semibold text-amber-800 text-sm">
                                Action Required:{' '}
                              </span>
                              <span className="text-amber-900 text-sm">
                                {change.ai_action}
                              </span>
                            </div>
                          )}
                          <div>
                            <div className="text-xs font-semibold text-gray-500 uppercase mb-1">
                              Diff ({change.diff_line_count} lines changed)
                            </div>
                            <DiffViewer
                              diff={change.diff_text || ''}
                              maxLines={100}
                            />
                          </div>
                          {change.sharepoint_item_id && (
                            <div className="text-xs text-gray-500">
                              SharePoint Item ID: {change.sharepoint_item_id}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
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
    </div>
  )
}
