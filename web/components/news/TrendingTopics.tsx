'use client'

interface Trend {
  topic: string
  mention_count: number
  growth_rate: number
  status: string
  categories: string[]
}

interface TrendingTopicsProps {
  trends: Trend[]
}

const STATUS_COLORS: Record<string, string> = {
  explosive: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  rising: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  emerging: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  stable: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

export function TrendingTopics({ trends }: TrendingTopicsProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-xl">🔥</span>
          Trending Topics
        </h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">Last 7 days</span>
      </div>

      {!trends || trends.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
          No trending topics yet
        </p>
      ) : (
        <div className="space-y-3">
          {trends.slice(0, 8).map((trend, index) => (
            <div
              key={trend.topic}
              className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition cursor-pointer"
            >
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">
                {index + 1}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                    {trend.topic}
                  </h4>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${STATUS_COLORS[trend.status] || STATUS_COLORS.stable}`}>
                    {trend.status}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <span>{trend.mention_count} mentions</span>
                  <span>•</span>
                  <span className="text-green-600 dark:text-green-400 font-medium">
                    +{(trend.growth_rate * 100).toFixed(0)}%
                  </span>
                </div>

                {trend.categories && trend.categories.length > 0 && (
                  <div className="flex gap-1 mt-1">
                    {trend.categories.slice(0, 2).map((cat) => (
                      <span
                        key={cat}
                        className="text-xs text-gray-400 dark:text-gray-500 capitalize"
                      >
                        #{cat}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
