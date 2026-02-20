'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { NewsList } from '@/components/news/NewsList'
import { TrendingTopics } from '@/components/news/TrendingTopics'
import { CategoryFilter } from '@/components/news/CategoryFilter'

const CATEGORIES = [
  'all',
  'technology',
  'science',
  'health',
  'business',
  'politics',
  'sports',
  'entertainment',
  'environment'
]

export default function NewsPage() {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [articles, setArticles] = useState([])
  const [trends, setTrends] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    fetchNews()
    fetchTrends()
    fetchStats()
  }, [selectedCategory])

  const fetchNews = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: '20',
        offset: '0',
        ...(selectedCategory !== 'all' && { category: selectedCategory })
      })

      const response = await fetch(`/api/v1/news/articles?${params}`)
      const data = await response.json()

      if (data.success) {
        setArticles(data.articles || [])
      }
    } catch (error) {
      console.error('Error fetching news:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTrends = async () => {
    try {
      const response = await fetch('/api/v1/trends/trending?time_window=7&limit=10')
      const data = await response.json()

      if (data.success) {
        setTrends(data.trends || [])
      }
    } catch (error) {
      console.error('Error fetching trends:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/news/stats')
      const data = await response.json()

      if (data.success) {
        setStats(data.stats)
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
              <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                DeepTutorNews
              </Link>
              <span className="px-3 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full">
                AI-Powered
              </span>
            </div>

            <nav className="hidden md:flex items-center space-x-6">
              <Link href="/news" className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700">
                Latest News
              </Link>
              <Link href="/news/fact-check" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                Fact Check
              </Link>
              <Link href="/news/trends" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                Trends
              </Link>
              <Link href="/" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                Deep Research
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Bar */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {stats.total_articles?.toLocaleString() || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Articles</div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {Object.keys(stats.by_source || {}).length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">News Sources</div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {Object.keys(stats.by_language || {}).length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Languages</div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {stats.storage_size_mb || 0} MB
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Storage Used</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - News Feed */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Latest News
              </h1>
              <button
                onClick={fetchNews}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                🔄 Refresh
              </button>
            </div>

            {/* Category Filter */}
            <CategoryFilter
              categories={CATEGORIES}
              selected={selectedCategory}
              onChange={setSelectedCategory}
            />

            {/* News List */}
            <NewsList articles={articles} loading={loading} />
          </div>

          {/* Right Column - Trending */}
          <div className="space-y-6">
            <TrendingTopics trends={trends} />

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <Link
                  href="/news/fact-check"
                  className="block w-full px-4 py-3 text-sm font-medium text-center text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition"
                >
                  ✓ Fact Check Article
                </Link>
                <Link
                  href="/news/trends"
                  className="block w-full px-4 py-3 text-sm font-medium text-center text-blue-600 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition"
                >
                  📈 View All Trends
                </Link>
                <button
                  onClick={() => fetch('/api/v1/news/fetch', { method: 'POST' })}
                  className="block w-full px-4 py-3 text-sm font-medium text-center text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition"
                >
                  🔄 Fetch Latest News
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
