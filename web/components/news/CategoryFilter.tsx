'use client'

interface CategoryFilterProps {
  categories: string[]
  selected: string
  onChange: (category: string) => void
}

const CATEGORY_ICONS: Record<string, string> = {
  all: '📰',
  technology: '💻',
  science: '🔬',
  health: '🏥',
  business: '💼',
  politics: '🏛️',
  sports: '⚽',
  entertainment: '🎬',
  environment: '🌍'
}

export function CategoryFilter({ categories, selected, onChange }: CategoryFilterProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => onChange(category)}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition flex items-center gap-2
              ${selected === category
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }
            `}
          >
            <span>{CATEGORY_ICONS[category] || '📄'}</span>
            <span className="capitalize">{category}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
