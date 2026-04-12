import { FeedItem } from '@/lib/types';

interface TopicCardProps {
  item: FeedItem;
  onFeedback?: (action: string) => void;
  onModeSwitch?: (mode: string) => void;
}

export default function TopicCard({ item, onFeedback, onModeSwitch }: TopicCardProps) {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl p-6 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
          {item.presentation_mode}
        </span>
        <span className="text-xs text-gray-500">
          {item.source_count} sources merged
        </span>
      </div>
      <h2 className="text-xl font-bold mb-2">{item.topic_label}</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-3">{item.summary}</p>
      {item.why_it_matters && (
        <p className="text-sm text-blue-600 dark:text-blue-400 mb-3 italic">
          Why it matters: {item.why_it_matters}
        </p>
      )}
      <div className="flex gap-2 mb-3">
        {item.source_links?.map((link, i) => (
          <a
            key={i}
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-500 hover:text-blue-500 underline"
          >
            {link.source}
          </a>
        ))}
      </div>
      <div className="flex items-center gap-3 pt-3 border-t border-gray-100 dark:border-gray-800">
        <button onClick={() => onFeedback?.('like')} className="text-sm hover:bg-gray-100 dark:hover:bg-gray-800 px-2 py-1 rounded">
          👍
        </button>
        <button onClick={() => onFeedback?.('dislike')} className="text-sm hover:bg-gray-100 dark:hover:bg-gray-800 px-2 py-1 rounded">
          👎
        </button>
        <button onClick={() => onFeedback?.('save')} className="text-sm hover:bg-gray-100 dark:hover:bg-gray-800 px-2 py-1 rounded">
          🔖
        </button>
        <div className="ml-auto flex gap-1">
          {['news', 'explainer_basics', 'explainer_delta', 'discussion'].map((mode) => (
            <button
              key={mode}
              onClick={() => onModeSwitch?.(mode)}
              className={`text-xs px-2 py-1 rounded ${
                item.presentation_mode === mode
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}
            >
              {mode.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
