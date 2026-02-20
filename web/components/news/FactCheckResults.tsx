'use client'

interface Claim {
  claim: string
  type: string
  verification: {
    verdict: string
    confidence: number
    reasoning: string
  }
  credibility_score: number
  evidence: any[]
}

interface FactCheckResult {
  article_title: string
  claims: Claim[]
  bias_analysis: {
    political_lean: string
    political_confidence: number
    emotional_tone: string
    loaded_language: string[]
    overall_bias_score: number
  }
  overall_credibility: number
  summary: {
    claims_checked: number
    verdicts: Record<string, number>
  }
}

interface FactCheckResultsProps {
  result: FactCheckResult
}

const VERDICT_COLORS: Record<string, string> = {
  true: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  false: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  misleading: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  unverifiable: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

const VERDICT_ICONS: Record<string, string> = {
  true: '✓',
  false: '✗',
  misleading: '⚠',
  unverifiable: '?'
}

export function FactCheckResults({ result }: FactCheckResultsProps) {
  const getCredibilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400'
    if (score >= 0.6) return 'text-blue-600 dark:text-blue-400'
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getBiasColor = (score: number) => {
    if (score < 0.3) return 'text-green-600 dark:text-green-400'
    if (score < 0.6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  return (
    <div className="space-y-8">
      {/* Overall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Overall Credibility</div>
          <div className={`text-3xl font-bold ${getCredibilityColor(result.overall_credibility)}`}>
            {(result.overall_credibility * 100).toFixed(0)}%
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Claims Checked</div>
          <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
            {result.summary.claims_checked}
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Bias Score</div>
          <div className={`text-3xl font-bold ${getBiasColor(result.bias_analysis.overall_bias_score)}`}>
            {(result.bias_analysis.overall_bias_score * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Verdict Distribution */}
      {result.summary.verdicts && Object.keys(result.summary.verdicts).length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Verdict Distribution</h3>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(result.summary.verdicts).map(([verdict, count]) => (
              <div key={verdict} className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${VERDICT_COLORS[verdict]}`}>
                  {VERDICT_ICONS[verdict]} {verdict}
                </span>
                <span className="text-gray-600 dark:text-gray-400 text-sm">×{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bias Analysis */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Bias Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Political Lean</div>
            <div className="text-sm font-medium capitalize">
              {result.bias_analysis.political_lean}
              <span className="text-gray-500 dark:text-gray-400 ml-2">
                ({(result.bias_analysis.political_confidence * 100).toFixed(0)}% confidence)
              </span>
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Emotional Tone</div>
            <div className="text-sm font-medium capitalize">
              {result.bias_analysis.emotional_tone}
            </div>
          </div>
        </div>

        {result.bias_analysis.loaded_language && result.bias_analysis.loaded_language.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Loaded Language Detected:</div>
            <div className="flex gap-2 flex-wrap">
              {result.bias_analysis.loaded_language.slice(0, 5).map((word, i) => (
                <span key={i} className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 rounded text-xs">
                  {word}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Claims */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Verified Claims</h3>

        {result.claims && result.claims.length > 0 ? (
          result.claims.map((claim, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
              {/* Claim Header */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex-1">
                  <p className="text-gray-900 dark:text-white font-medium mb-2">
                    "{claim.claim}"
                  </p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded capitalize">
                      {claim.type}
                    </span>
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${VERDICT_COLORS[claim.verification.verdict]}`}>
                      {VERDICT_ICONS[claim.verification.verdict]} {claim.verification.verdict}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {(claim.verification.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
              </div>

              {/* Reasoning */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 mb-3">
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Analysis</div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {claim.verification.reasoning}
                </p>
              </div>

              {/* Evidence Count */}
              {claim.evidence && claim.evidence.length > 0 && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Based on {claim.evidence.length} source{claim.evidence.length !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No claims were extracted from this article
          </div>
        )}
      </div>
    </div>
  )
}
