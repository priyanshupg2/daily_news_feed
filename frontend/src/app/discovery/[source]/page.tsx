'use client';

import { useEffect, useState } from 'react';
import { use } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { DiscoveryListItem, PaginatedResponse, DiscoveryGroupsResponse } from '@/lib/types';
import ItemRow from '@/components/discovery/ItemRow';

const SOURCE_LABELS: Record<string, string> = {
  arxiv: 'arXiv',
  hackernews: 'Hacker News',
  reddit: 'Reddit',
  github: 'GitHub',
  semanticscholar: 'Semantic Scholar',
  techblogs: 'Tech Blogs',
  techcrunch: 'TechCrunch',
  conferences: 'Conferences',
};

// Sources that have sub-groups (show grouped view first)
const GROUPED_SOURCES: Record<string, string> = {
  techblogs: 'blog',
  conferences: 'venue',
};

const PAGE_SIZE = 50;

export default function SourceListPage({
  params,
}: {
  params: Promise<{ source: string }>;
}) {
  const { source } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const date = searchParams.get('date') || new Date().toISOString().slice(0, 10);
  const group = searchParams.get('group');

  const isGroupedSource = source in GROUPED_SOURCES;
  const showGroups = isGroupedSource && !group;

  if (showGroups) {
    return <GroupedView source={source} date={date} />;
  }

  return <ItemListView source={source} date={date} group={group} />;
}

function GroupedView({ source, date }: { source: string; date: string }) {
  const [data, setData] = useState<DiscoveryGroupsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const groupKey = GROUPED_SOURCES[source];
    api.getDiscoveryGroups(source, date, groupKey).then(setData).finally(() => setLoading(false));
  }, [source, date]);

  const totalItems = data ? data.groups.reduce((sum, g) => sum + g.count, 0) : 0;

  return (
    <main className="max-w-lg mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/discovery" className="text-sm text-gray-400 hover:text-gray-600">
          &larr; Discovery
        </Link>
        <h1 className="text-2xl font-bold mt-1">{SOURCE_LABELS[source] || source}</h1>
        <p className="text-gray-500 text-sm">
          {date} &middot; {totalItems} items across {data?.groups.length || 0} blogs
        </p>
      </div>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : data && data.groups.length > 0 ? (
        <div className="space-y-3">
          {data.groups.map((g) => (
            <Link
              key={g.name}
              href={`/discovery/${source}?date=${date}&group=${encodeURIComponent(g.name)}`}
              className="block border border-gray-200 rounded-lg px-5 py-4 hover:border-gray-400 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">{g.name}</span>
                <span className="text-lg font-semibold tabular-nums text-gray-700">{g.count}</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="border border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-400 text-sm">
          No items found.
        </div>
      )}
    </main>
  );
}

function ItemListView({
  source,
  date,
  group,
}: {
  source: string;
  date: string;
  group: string | null;
}) {
  const [data, setData] = useState<PaginatedResponse<DiscoveryListItem> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);

  const isGrouped = source in GROUPED_SOURCES;

  useEffect(() => {
    setLoading(true);
    api
      .getDiscoveryItems(source, {
        date,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        group: group || undefined,
        groupKey: source in GROUPED_SOURCES ? GROUPED_SOURCES[source] : undefined,
      })
      .then(setData)
      .finally(() => setLoading(false));
  }, [source, date, page, group]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  // Back link: if viewing a group, go back to the grouped view; otherwise go to dashboard
  const backHref = isGrouped && group
    ? `/discovery/${source}?date=${date}`
    : '/discovery';
  const backLabel = isGrouped && group
    ? `\u2190 ${SOURCE_LABELS[source] || source}`
    : '\u2190 Discovery';

  return (
    <main className="max-w-lg mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href={backHref} className="text-sm text-gray-400 hover:text-gray-600">
          {backLabel}
        </Link>
        <h1 className="text-2xl font-bold mt-1">
          {group || SOURCE_LABELS[source] || source}
        </h1>
        <p className="text-gray-500 text-sm">
          {date} &middot; {data ? `${data.total} items` : '...'}
        </p>
      </div>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : data && data.items.length > 0 ? (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          {data.items.map((item) => (
            <ItemRow
              key={item.id}
              id={item.id}
              title={item.title}
              publishedAt={item.published_at}
            />
          ))}
        </div>
      ) : (
        <div className="border border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-400 text-sm">
          No items found.
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 0}
            className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-30"
          >
            &larr;
          </button>
          <span className="text-sm text-gray-500">
            {page + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-30"
          >
            &rarr;
          </button>
        </div>
      )}
    </main>
  );
}
