interface StatusBadgeProps {
  status: string
  type?: 'status' | 'priority'
}

const STATUS_STYLES: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800',
  in_review: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
  false_positive: 'bg-gray-100 text-gray-600',
  success: 'bg-green-100 text-green-700',
  changed: 'bg-orange-100 text-orange-700',
  error: 'bg-red-100 text-red-700',
  timeout: 'bg-red-100 text-red-600',
  skipped: 'bg-gray-100 text-gray-500',
}

const PRIORITY_STYLES: Record<string, string> = {
  high: 'bg-red-100 text-red-800 font-semibold',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-600',
}

export default function StatusBadge({ status, type = 'status' }: StatusBadgeProps) {
  const styles =
    type === 'priority'
      ? PRIORITY_STYLES[status] || 'bg-gray-100 text-gray-600'
      : STATUS_STYLES[status] || 'bg-gray-100 text-gray-600'

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs capitalize ${styles}`}
    >
      {status.replace('_', ' ')}
    </span>
  )
}
