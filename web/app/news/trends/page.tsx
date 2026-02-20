'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { TrendChart } from '@/components/news/TrendChart'
import { SentimentChart } from '@/components/news/SentimentChart'
import { TrendCard } from '@/components/news/TrendCard'

export default function TrendsPage() {
  const [trends, setTrends] = useState([])
  const [selectedTrend, setSelectedTrend] = useState<any>(null)
  const [timeline, setTimeline] = useState([])
  const [sentiment, setSentiment] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [timeWindow, setTimeWindow] = useState(7)

  useEffect(() => {
    fetchTrends()
    fetchStats()
  }, [timeWindow])

  useEffect(() => {
    if (selectedTrend) {
      fetchTimeline(selectedTrend.topic)
      fetchSentiment(selectedTrend.topic)
    }
  }, [selectedTrend])

  const fetchTrends = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/v1/trends/trending?time_window=${timeWindow}&limit=20`)
      const data = await response.json()

      if (data.success && data.trends.length > 0) {
        setTrends(data.trends)
        setSelectedTrend(data.trends[0])
      }
    } catch (error) {
      console.error('Error fetching trends:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTimeline = async (topic: string) => {
    try {
      const response = await fetch(`/api/v1/trends/timeline/${encodeURIComponent(topic)}?days=30`)
      const data = await response.json()

      if (data.success) {
        setTimeline(data.timeline || [])
      }
    } catch (error) {
      console.error('Error fetching timeline:', error)
    }
  }

  const fetchSentiment = async (topic: string) => {
    try {
      const response = await fetch('/api/v1/trends/sentiment/topic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, days: 30 })
      })

      const data = await response.json()

      if (data.success) {
        setSentiment(data)
      }
    } catch (error) {
      console.error('Error fetching sentiment:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/v1/trends/stats?days=${timeWindow}`)
      const data = await response.json()

      if (data.success) {
        setStats(data)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-slate-900">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/news" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                DeepTutorNews
              </Link>
              <span className="text-gray-400">|</span>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                📈 Trend Analysis
              </h1>
            </div>

            <div className="flex items-center gap-4">
              <select
                value={timeWindow}
                onChange={(e) => setTimeWindow(Number(e.target.value))}
                className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
              >
                <option value={1}>Last 24 hours</option>
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
              </select>

              <Link
                href="/news"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                ← Back to News
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {stats.trending_topics || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Trending Topics</div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {stats.total_articles?.toLocaleString() || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Articles Analyzed</div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                {stats.average_sentiment?.positive ? (stats.average_sentiment.positive * 100).toFixed(0) : 0}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Avg Positive Sentiment</div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                {timeWindow}d
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Time Window</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Trends List */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Trending Topics ({trends.length})
            </h2>

            {loading ? (
              <div className="space-y-3">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm animate-pulse">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : trends.length === 0 ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-sm text-center">
                <div className="text-4xl mb-2">📊</div>
                <p className="text-gray-600 dark:text-gray-400">No trends detected yet</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto">
                {trends.map((trend: any, index) => (
                  <TrendCard
                    key={trend.topic}
                    trend={trend}
                    rank={index + 1}
                    selected={selectedTrend?.topic === trend.topic}
                    onClick={() => setSelectedTrend(trend)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Right: Detailed Analysis */}
          <div className="lg:col-span-2 space-y-6">
            {selectedTrend ? (
              <>
                {/* Topic Header */}
                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    {selectedTrend.topic}
                  </h2>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Mentions</div>
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {selectedTrend.mention_count}
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Growth Rate</div>
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        +{(selectedTrend.growth_rate * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
                      <div className="text-2xl font-bold text-orange-600 dark:text-orange-400 capitalize">
                        {selectedTrend.status}
                      </div>
                    </div>
                  </div>

                  {selectedTrend.categories && selectedTrend.categories.length > 0 && (
                    <div className="mt-4 flex gap-2 flex-wrap">
                      {selectedTrend.categories.map((cat: string) => (
                        <span
                          key={cat}
                          className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm capitalize"
                        >
                          {cat}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Timeline Chart */}
                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Mention Timeline
                  </h3>
                  <TrendChart data={timeline} />
                </div>

                {/* Sentiment Chart */}
                {sentiment && sentiment.timeline && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Sentiment Analysis
                    </h3>
                    <SentimentChart
                      data={sentiment.timeline}
                      overall={sentiment.overall_sentiment}
                      trend={sentiment.sentiment_trend}
                    />
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-12 shadow-sm text-center">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Select a Topic
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Choose a trending topic from the list to see detailed analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
