interface DiffViewerProps {
  diff: string
  maxLines?: number
}

export default function DiffViewer({ diff, maxLines }: DiffViewerProps) {
  if (!diff) {
    return (
      <div className="text-gray-400 text-sm italic p-3">No diff available</div>
    )
  }

  const lines = diff.split('\n')
  const displayLines = maxLines ? lines.slice(0, maxLines) : lines
  const truncated = maxLines && lines.length > maxLines

  return (
    <div className="font-mono text-xs overflow-x-auto border border-gray-200 rounded-md bg-gray-50">
      <div className="overflow-y-auto max-h-96">
        {displayLines.map((line, i) => {
          let bg = ''
          let textColor = 'text-gray-700'

          if (line.startsWith('+') && !line.startsWith('+++')) {
            bg = 'bg-green-50'
            textColor = 'text-green-800'
          } else if (line.startsWith('-') && !line.startsWith('---')) {
            bg = 'bg-red-50'
            textColor = 'text-red-800'
          } else if (line.startsWith('@@')) {
            bg = 'bg-blue-50'
            textColor = 'text-blue-700'
          } else if (line.startsWith('---') || line.startsWith('+++')) {
            bg = 'bg-gray-100'
            textColor = 'text-gray-500'
          }

          return (
            <div
              key={i}
              className={`flex whitespace-pre px-3 py-0.5 ${bg} ${textColor}`}
            >
              <span className="select-none text-gray-400 w-10 shrink-0 text-right mr-3">
                {i + 1}
              </span>
              <span>{line}</span>
            </div>
          )
        })}
      </div>
      {truncated && (
        <div className="px-3 py-2 text-center text-gray-400 text-xs border-t border-gray-200 bg-white">
          ... {lines.length - maxLines!} more lines
        </div>
      )}
    </div>
  )
}
