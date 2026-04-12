'use client';

import Link from 'next/link';

const SOURCE_LABELS: Record<string, string> = {
  arxiv: 'arXiv',
  hackernews: 'Hacker News',
  reddit: 'Reddit',
  github: 'GitHub',
  semanticscholar: 'Semantic Scholar',
  techblogs: 'Tech Blogs',
  techcrunch: 'TechCrunch',
};

export default function SourceCard({
  source,
  count,
  date,
}: {
  source: string;
  count: number;
  date: string;
}) {
  return (
    <Link
      href={`/discovery/${source}?date=${date}`}
      className="block border border-gray-200 rounded-lg px-5 py-4 hover:border-gray-400 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-center justify-between">
        <span className="text-lg font-medium text-gray-900">
          {SOURCE_LABELS[source] || source}
        </span>
        <span className="text-2xl font-semibold tabular-nums text-gray-700">
          {count}
        </span>
      </div>
    </Link>
  );
}
