'use client'

import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'

interface Article {
  id: string
  title: string
  description?: string
  source_name: string
  category: string
  published_at: string
  image_url?: string
  url?: string
  credibility_score?: number
  language?: string
}

interface NewsCardProps {
  article: Article
}

const CATEGORY_COLORS: Record<string, string> = {
  technology: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  science: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  health: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  business: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  politics: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  sports: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  entertainment: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300',
  environment: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  general: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

export function NewsCard({ article }: NewsCardProps) {
  const categoryColor = CATEGORY_COLORS[article.category] || CATEGORY_COLORS.general

  const getTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return 'recently'
    }
  }

  const getCredibilityBadge = (score?: number) => {
    if (!score) return null

    if (score >= 0.9) {
      return <span className="text-xs font-medium text-green-600 dark:text-green-400">✓ Highly Credible</span>
    } else if (score >= 0.7) {
      return <span className="text-xs font-medium text-blue-600 dark:text-blue-400">✓ Credible</span>
    } else if (score >= 0.5) {
      return <span className="text-xs font-medium text-yellow-600 dark:text-yellow-400">⚠ Mixed</span>
    }
    return <span className="text-xs font-medium text-red-600 dark:text-red-400">⚠ Low Credibility</span>
  }

  return (
    <article className="group bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
      <Link href={`/news/article/${article.id}`}>
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition line-clamp-2 mb-2">
                {article.title}
              </h2>
              <div className="flex items-center gap-3 flex-wrap text-sm">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColor}`}>
                  {article.category}
                </span>
                <span className="text-gray-600 dark:text-gray-400">
                  {article.source_name}
                </span>
                <span className="text-gray-400 dark:text-gray-500">
                  {getTimeAgo(article.published_at)}
                </span>
                {article.language && article.language !== 'en' && (
                  <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                    {article.language}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {article.description && (
            <p className="text-gray-600 dark:text-gray-300 line-clamp-3 mb-4">
              {article.description}
            </p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-4">
              {getCredibilityBadge(article.credibility_score)}
              <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium">
                Read more →
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.preventDefault()
                  navigator.clipboard.writeText(window.location.origin + `/news/article/${article.id}`)
                }}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
                title="Copy link"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>

              {article.url && (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
                  title="Open original"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>
          </div>
        </div>
      </Link>
    </article>
  )
}
