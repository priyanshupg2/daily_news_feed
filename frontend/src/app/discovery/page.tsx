'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { DiscoveryStats } from '@/lib/types';
import SourceCard from '@/components/discovery/SourceCard';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function shiftDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T00:00:00');
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function DiscoveryPage() {
  const [date, setDate] = useState(todayStr);
  const [stats, setStats] = useState<DiscoveryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getDiscoveryStats(date).then(setStats).finally(() => setLoading(false));
  }, [date]);

  async function handleRunDiscovery() {
    setRunning(true);
    try {
      await api.runDiscovery();
      const fresh = await api.getDiscoveryStats(date);
      setStats(fresh);
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-1">Discovery</h1>
      <p className="text-gray-500 text-sm mb-6">Raw items fetched from external sources</p>

      {/* Date picker */}
      <div className="flex items-center gap-3 mb-8">
        <button
          onClick={() => setDate(shiftDate(date, -1))}
          className="px-2 py-1 text-gray-500 hover:text-gray-900 text-lg"
        >
          &#9664;
        </button>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
        />
        <button
          onClick={() => setDate(shiftDate(date, 1))}
          disabled={date >= todayStr()}
          className="px-2 py-1 text-gray-500 hover:text-gray-900 text-lg disabled:opacity-30"
        >
          &#9654;
        </button>
      </div>

      {/* Source cards */}
      {loading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : (
        <div className="space-y-3 mb-8">
          {stats && stats.sources.length > 0 ? (
            stats.sources.map((s) => (
              <SourceCard key={s.source} source={s.source} count={s.count} date={date} />
            ))
          ) : (
            <div className="border border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-400 text-sm">
              No items fetched for this date.
            </div>
          )}
        </div>
      )}

      {/* Footer stats */}
      {stats && stats.total > 0 && (
        <div className="text-xs text-gray-400 mb-6">
          Total: {stats.total} items
          {stats.latest_fetch && (
            <>
              {' '}&middot; Last fetched: {new Date(stats.latest_fetch).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </>
          )}
        </div>
      )}

      {/* Run discovery */}
      <button
        onClick={handleRunDiscovery}
        disabled={running}
        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
      >
        {running ? 'Running...' : 'Run Discovery'}
      </button>
    </main>
  );
}
