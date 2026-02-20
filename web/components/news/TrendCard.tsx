'use client'

interface TrendCardProps {
  trend: {
    topic: string
    mention_count: number
    growth_rate: number
    status: string
    categories: string[]
  }
  rank: number
  selected: boolean
  onClick: () => void
}

const STATUS_COLORS: Record<string, string> = {
  explosive: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  rising: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  emerging: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  stable: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

export function TrendCard({ trend, rank, selected, onClick }: TrendCardProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left p-4 rounded-lg transition-all
        ${selected
          ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500 shadow-md'
          : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:shadow-md'
        }
      `}
    >
      <div className="flex items-start gap-3">
        {/* Rank Badge */}
        <div className={`
          flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
          ${rank <= 3
            ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
          }
        `}>
          {rank}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 line-clamp-1">
            {trend.topic}
          </h3>

          <div className="flex items-center gap-3 flex-wrap mb-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[trend.status] || STATUS_COLORS.stable}`}>
              {trend.status}
            </span>

            <span className="text-xs text-gray-500 dark:text-gray-400">
              {trend.mention_count} mentions
            </span>

            <span className="text-xs font-medium text-green-600 dark:text-green-400">
              +{(trend.growth_rate * 100).toFixed(0)}%
            </span>
          </div>

          {/* Categories */}
          {trend.categories && trend.categories.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              {trend.categories.slice(0, 2).map((cat) => (
                <span key={cat} className="text-xs text-gray-400 dark:text-gray-500 capitalize">
                  #{cat}
                </span>
              ))}
              {trend.categories.length > 2 && (
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  +{trend.categories.length - 2}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}
