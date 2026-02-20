'use client'

import { NewsCard } from './NewsCard'

interface Article {
  id: string
  title: string
  description?: string
  content?: string
  source_name: string
  category: string
  published_at: string
  image_url?: string
  url?: string
  credibility_score?: number
  language?: string
}

interface NewsListProps {
  articles: Article[]
  loading: boolean
}

export function NewsList({ articles, loading }: NewsListProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!articles || articles.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-12 shadow-sm text-center">
        <div className="text-6xl mb-4">📰</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          No Articles Found
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Try selecting a different category or fetch new articles
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {articles.map((article) => (
        <NewsCard key={article.id} article={article} />
      ))}
    </div>
  )
}
