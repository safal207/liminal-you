import { useEffect, useMemo, useState } from 'react';
import { getSnapshots, getTrends } from '../api/client';
import type { Snapshot, TrendsResponse } from '../types';
import TrendChart from './TrendChart';

export default function AnalyticsDashboard() {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let canceled = false;
    (async () => {
      try {
        const [s, t] = await Promise.all([getSnapshots(100), getTrends(3600)]);
        if (!canceled) {
          setSnapshots(s);
          setTrends(t);
        }
      } catch (e) {
        if (!canceled) setError('Failed to load analytics');
      }
    })();
    return () => {
      canceled = true;
    };
  }, []);

  const data = useMemo(() => {
    return snapshots.map((s) => ({
      t: new Date(s.timestamp * 1000).toLocaleTimeString(),
      entropy: s.entropy,
      coherence: s.coherence,
    }));
  }, [snapshots]);

  if (error) return <div className="text-sm text-red-400">{error}</div>;

  return (
    <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
      <div className="mb-2 text-accent">Analytics</div>
      <TrendChart data={data} />
      {trends && (
        <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
          <div>
            <div className="opacity-70">Entropy</div>
            <div>{trends.entropy_trend} ({trends.entropy_change.toFixed(2)})</div>
          </div>
          <div>
            <div className="opacity-70">Coherence</div>
            <div>{trends.coherence_trend} ({trends.coherence_change.toFixed(2)})</div>
          </div>
          <div>
            <div className="opacity-70">Overall mood</div>
            <div>{trends.overall_mood}</div>
          </div>
        </div>
      )}
    </div>
  );
}

