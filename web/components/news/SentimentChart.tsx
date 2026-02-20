'use client'

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface SentimentChartProps {
  data: Array<{
    date: string
    positive: number
    negative: number
    neutral: number
    article_count: number
  }>
  overall: {
    positive: number
    negative: number
    neutral: number
  }
  trend: string
}

export function SentimentChart({ data, overall, trend }: SentimentChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="space-y-4">
        {/* Overall Sentiment */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Positive</div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {(overall.positive * 100).toFixed(0)}%
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Neutral</div>
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {(overall.neutral * 100).toFixed(0)}%
            </div>
          </div>

          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Negative</div>
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {(overall.negative * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
          <p>No sentiment timeline data available</p>
        </div>
      </div>
    )
  }

  const getTrendBadge = (trend: string) => {
    const colors = {
      improving: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      declining: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      stable: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }

    const icons = {
      improving: '↗',
      declining: '↘',
      stable: '→'
    }

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[trend] || colors.stable}`}>
        {icons[trend] || '→'} {trend}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Overall Stats */}
      <div className="flex items-center justify-between">
        <div className="grid grid-cols-3 gap-4 flex-1">
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Overall Positive</div>
            <div className="text-xl font-bold text-green-600 dark:text-green-400">
              {(overall.positive * 100).toFixed(0)}%
            </div>
          </div>

          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Overall Negative</div>
            <div className="text-xl font-bold text-red-600 dark:text-red-400">
              {(overall.negative * 100).toFixed(0)}%
            </div>
          </div>

          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Trend</div>
            <div>{getTrendBadge(trend)}</div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis
            dataKey="date"
            stroke="#9CA3AF"
            fontSize={12}
            tickFormatter={(value) => {
              const date = new Date(value)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }}
          />
          <YAxis stroke="#9CA3AF" fontSize={12} domain={[0, 1]} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: 'none',
              borderRadius: '8px',
              color: '#F9FAFB'
            }}
            labelFormatter={(value) => {
              const date = new Date(value)
              return date.toLocaleDateString()
            }}
            formatter={(value: any) => `${(value * 100).toFixed(1)}%`}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="positive"
            stackId="1"
            stroke="#10B981"
            fill="#10B981"
            fillOpacity={0.6}
            name="Positive"
          />
          <Area
            type="monotone"
            dataKey="neutral"
            stackId="1"
            stroke="#6B7280"
            fill="#6B7280"
            fillOpacity={0.4}
            name="Neutral"
          />
          <Area
            type="monotone"
            dataKey="negative"
            stackId="1"
            stroke="#EF4444"
            fill="#EF4444"
            fillOpacity={0.6}
            name="Negative"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
