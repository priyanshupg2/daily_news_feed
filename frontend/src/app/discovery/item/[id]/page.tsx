'use client';

import { useEffect, useState } from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { RawItem } from '@/lib/types';

const SOURCE_LABELS: Record<string, string> = {
  arxiv: 'arXiv',
  hackernews: 'Hacker News',
  reddit: 'Reddit',
  github: 'GitHub',
  semanticscholar: 'Semantic Scholar',
  techblogs: 'Tech Blogs',
  techcrunch: 'TechCrunch',
};

export default function ItemDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [item, setItem] = useState<RawItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .getDiscoveryItem(id)
      .then(setItem)
      .catch(() => setError('Item not found'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <main className="max-w-lg mx-auto px-4 py-8">
        <p className="text-gray-400 text-sm">Loading...</p>
      </main>
    );
  }

  if (error || !item) {
    return (
      <main className="max-w-lg mx-auto px-4 py-8">
        <button onClick={() => router.back()} className="text-sm text-gray-400 hover:text-gray-600">
          &larr; Back
        </button>
        <p className="text-gray-500 mt-4">{error || 'Item not found'}</p>
      </main>
    );
  }

  return (
    <main className="max-w-lg mx-auto px-4 py-8">
      {/* Back */}
      <button onClick={() => router.back()} className="text-sm text-gray-400 hover:text-gray-600 mb-4 block">
        &larr; Back
      </button>

      {/* Title */}
      <h1 className="text-xl font-bold leading-snug mb-4">{item.title}</h1>

      {/* Fields */}
      <dl className="space-y-2 text-sm mb-6">
        <Row label="Source" value={SOURCE_LABELS[item.source] || item.source} />
        {item.authors && <Row label="Authors" value={item.authors} />}
        {item.published_at && (
          <Row label="Published" value={new Date(item.published_at).toLocaleString()} />
        )}
        <Row label="Fetched" value={item.fetch_date} />
        {item.url && (
          <div className="flex gap-3">
            <dt className="w-24 flex-shrink-0 text-gray-400">URL</dt>
            <dd>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline break-all"
              >
                {item.url}
              </a>
            </dd>
          </div>
        )}
      </dl>

      {/* Content */}
      {item.content && (
        <div className="mb-6">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
            Content
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {item.content}
          </p>
        </div>
      )}

      {/* Metadata */}
      {item.metadata && Object.keys(item.metadata).length > 0 && (
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
            Metadata
          </h2>
          <dl className="space-y-1 text-sm">
            {Object.entries(item.metadata).map(([key, value]) => (
              <div key={key} className="flex gap-3">
                <dt className="w-32 flex-shrink-0 text-gray-400 font-mono text-xs mt-0.5">
                  {key}
                </dt>
                <dd className="text-gray-700 break-all">
                  {typeof value === 'string' && value.startsWith('http') ? (
                    <a href={value} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {value}
                    </a>
                  ) : (
                    String(Array.isArray(value) ? value.join(', ') : value)
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </main>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-24 flex-shrink-0 text-gray-400">{label}</dt>
      <dd className="text-gray-700">{value}</dd>
    </div>
  );
}
