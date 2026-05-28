import { useQuery } from '@tanstack/react-query'
import { getDashboard, getChanges } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import type { DashboardStats } from '../api/client'

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string
  value: number | string
  sub?: string
  color?: string
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className={`text-3xl font-bold ${color || 'text-gray-900'}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

function fmtDate(iso: string | null): string {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleString()
}

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    refetchInterval: 60_000,
  })

  const { data: recentChanges } = useQuery({
    queryKey: ['changes', 'recent'],
    queryFn: () => getChanges({ page_size: 10, page: 1 }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400">
        Loading...
      </div>
    )
  }
  if (error || !stats) {
    return (
      <div className="text-red-600 p-4">Failed to load dashboard stats.</div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Courts" value={stats.total_courts} />
        <StatCard
          label="Active Courts"
          value={stats.active_courts}
          sub={`${stats.total_courts - stats.active_courts} inactive`}
          color="text-blue-700"
        />
        <StatCard
          label="New Changes"
          value={stats.changes_new}
          sub="Awaiting review"
          color={stats.changes_new > 0 ? 'text-orange-600' : 'text-gray-900'}
        />
        <StatCard
          label="Errors This Week"
          value={stats.error_count}
          color={stats.error_count > 0 ? 'text-red-600' : 'text-gray-900'}
        />
        <StatCard
          label="Scanned Today"
          value={stats.scanned_today}
        />
        <StatCard
          label="Scanned This Week"
          value={stats.scanned_this_week}
        />
        <StatCard
          label="Changes This Week"
          value={stats.changes_this_week}
          color={stats.changes_this_week > 0 ? 'text-orange-600' : 'text-gray-900'}
        />
        <StatCard
          label="Last Scan"
          value={fmtDate(stats.last_scan_at)}
          color="text-gray-600"
        />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Recent Changes</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Court</th>
                <th className="px-4 py-3">Detected</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(recentChanges?.items || []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-400">
                    No recent changes detected
                  </td>
                </tr>
              )}
              {(recentChanges?.items || []).map((change) => (
                <tr key={change.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">
                    {change.court_name || `Court ${change.court_id}`}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(change.detected_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {change.ai_priority ? (
                      <StatusBadge status={change.ai_priority} type="priority" />
                    ) : (
                      <span className="text-gray-400 text-xs">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {change.ai_category || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={change.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
