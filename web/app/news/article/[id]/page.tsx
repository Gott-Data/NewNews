'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { FactCheckResults } from '@/components/news/FactCheckResults'

export default function ArticlePage() {
  const params = useParams()
  const router = useRouter()
  const articleId = params.id as string

  const [article, setArticle] = useState<any>(null)
  const [factCheck, setFactCheck] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState('quick')

  useEffect(() => {
    if (articleId) {
      fetchArticle()
    }
  }, [articleId])

  const fetchArticle = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/v1/news/article/${articleId}`)
      const data = await response.json()

      if (data.success) {
        setArticle(data.article)
      } else {
        console.error('Article not found')
      }
    } catch (error) {
      console.error('Error fetching article:', error)
    } finally {
      setLoading(false)
    }
  }

  const runFactCheck = async () => {
    setChecking(true)
    try {
      const response = await fetch('/api/v1/fact_check/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          article_id: articleId,
          preset: selectedPreset,
          max_claims: 5
        })
      })

      const data = await response.json()

      if (data.success) {
        setFactCheck(data.result)
      }
    } catch (error) {
      console.error('Error running fact-check:', error)
    } finally {
      setChecking(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-slate-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="animate-pulse space-y-8">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Article Not Found</h1>
          <Link href="/news" className="text-blue-600 dark:text-blue-400 hover:underline">
            ← Back to News
          </Link>
        </div>
      </div>
    )
  }

  const getTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return 'recently'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-slate-900">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link href="/news" className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to News
            </Link>

            <div className="flex items-center gap-4">
              <button
                onClick={() => window.open(article.url, '_blank')}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                View Original →
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Article Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <article>
          {/* Metadata */}
          <div className="flex items-center gap-3 mb-6 flex-wrap">
            <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium capitalize">
              {article.category}
            </span>
            <span className="text-gray-600 dark:text-gray-400 text-sm">
              {article.source_name}
            </span>
            <span className="text-gray-400 dark:text-gray-500 text-sm">
              {getTimeAgo(article.published_at)}
            </span>
            {article.language && (
              <span className="text-gray-500 dark:text-gray-400 text-xs uppercase">
                {article.language}
              </span>
            )}
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
            {article.title}
          </h1>

          {/* Description */}
          {article.description && (
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">
              {article.description}
            </p>
          )}

          {/* Content */}
          {article.content && (
            <div className="prose prose-lg dark:prose-invert max-w-none mb-12">
              <p className="whitespace-pre-wrap">{article.content}</p>
            </div>
          )}

          {/* Fact-Check Section */}
          <div className="mt-12 border-t border-gray-200 dark:border-gray-700 pt-12">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <span>✓</span> Fact Check
                </h2>

                <div className="flex items-center gap-3">
                  <select
                    value={selectedPreset}
                    onChange={(e) => setSelectedPreset(e.target.value)}
                    className="px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
                    disabled={checking}
                  >
                    <option value="quick">Quick (~10s)</option>
                    <option value="thorough">Thorough (~60s)</option>
                    <option value="deep">Deep (~2min)</option>
                  </select>

                  <button
                    onClick={runFactCheck}
                    disabled={checking}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {checking ? 'Checking...' : 'Run Fact Check'}
                  </button>
                </div>
              </div>

              {checking && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600 dark:text-gray-400">
                      Analyzing article with {selectedPreset} preset...
                    </p>
                  </div>
                </div>
              )}

              {!checking && factCheck && (
                <FactCheckResults result={factCheck} />
              )}

              {!checking && !factCheck && (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <p>Click "Run Fact Check" to verify claims in this article</p>
                </div>
              )}
            </div>
          </div>
        </article>
      </main>
    </div>
  )
}
