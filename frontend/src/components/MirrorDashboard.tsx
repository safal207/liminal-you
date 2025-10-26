import { useEffect, useMemo, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';
import { getMirrorStats } from '../api/client';
import { MirrorEventSummary, MirrorStats } from '../types';

const REFRESH_INTERVAL = 15000;

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
};

function HeatmapCell({ tone, intensity, reward }: { tone: string; intensity: number; reward: number }) {
  const color = reward >= 0 ? 'bg-emerald-400/30 border-emerald-300/40' : 'bg-rose-400/20 border-rose-300/30';
  return (
    <div className={`rounded-lg border p-3 text-center text-xs text-text ${color}`}>
      <div className="text-sm font-semibold text-accent">{tone}</div>
      <div className="mt-1 text-text/60">bin {intensity}</div>
      <div className="mt-1 text-accent">{reward.toFixed(2)}</div>
    </div>
  );
}

export default function MirrorDashboard() {
  const [stats, setStats] = useState<MirrorStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    const load = async () => {
      try {
        const data = await getMirrorStats();
        if (!cancelled) {
          setStats(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Не удалось получить статистику Mirror.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
          timer = window.setTimeout(load, REFRESH_INTERVAL);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, []);

  const chartData = useMemo(() => {
    if (!stats) {
      return [];
    }
    return [...stats.recent_events].reverse().map((event: MirrorEventSummary) => ({
      time: formatTime(event.ts),
      deltaCoherence: event.delta_coherence,
      deltaEntropy: event.delta_entropy,
    }));
  }, [stats]);

  const heatmap = useMemo(() => {
    if (!stats) {
      return [];
    }
    return stats.heatmap.sort((a, b) => a.intensity_bin - b.intensity_bin);
  }, [stats]);

  if (loading) {
    return <div className="rounded-xl border border-accent/30 bg-white/5 p-6 text-text/70">Загрузка Mirror…</div>;
  }

  if (error) {
    return <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-6 text-rose-100">{error}</div>;
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px] rounded-xl border border-accent/30 bg-black/20 p-4">
          <div className="text-sm uppercase tracking-widest text-accent/70">Покрытие</div>
          <div className="mt-2 text-2xl font-semibold text-accent">{Math.round(stats.bucket_coverage * 100)}%</div>
          <div className="text-xs text-text/60">Уникальных bucket’ов: {stats.unique_buckets}</div>
        </div>
        <div className="flex-1 min-w-[200px] rounded-xl border border-accent/30 bg-black/20 p-4">
          <div className="text-sm uppercase tracking-widest text-accent/70">Средний reward</div>
          <div className="mt-2 text-2xl font-semibold text-accent">{stats.avg_reward.toFixed(3)}</div>
          <div className="text-xs text-text/60">Всего эпизодов: {stats.total_events}</div>
        </div>
        <div className="flex-1 min-w-[200px] rounded-xl border border-accent/30 bg-black/20 p-4">
          <div className="text-sm uppercase tracking-widest text-accent/70">Текущая политика</div>
          {stats.current_policy ? (
            <div className="mt-2 space-y-1 text-sm text-text/80">
              <div>bucket: <span className="text-accent">{stats.current_policy.bucket_key}</span></div>
              <div>tone: <span className="text-accent">{stats.current_policy.tone}</span></div>
              <div>intensity bin: <span className="text-accent">{stats.current_policy.intensity_bin}</span></div>
            </div>
          ) : (
            <div className="mt-2 text-sm text-text/60">Пока нет обученной политики.</div>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-accent/30 bg-black/10 p-4">
        <div className="text-sm uppercase tracking-widest text-accent/70">Δ coherence / Δ entropy</div>
        <div className="h-64">
          {chartData.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff22" />
                <XAxis dataKey="time" stroke="#ffffff88" />
                <YAxis stroke="#ffffff88" domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ background: '#0f172a', borderRadius: 12, border: '1px solid #38bdf8' }} />
                <Line type="monotone" dataKey="deltaCoherence" stroke="#34d399" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="deltaEntropy" stroke="#f472b6" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-text/60">Недостаточно данных.</div>
          )}
        </div>
      </div>

      <div>
        <div className="text-sm uppercase tracking-widest text-accent/70">Эффективность по тону и интенсивности</div>
        {heatmap.length ? (
          <div className="mt-3 grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {heatmap.map((cell) => (
              <HeatmapCell
                key={`${cell.tone}-${cell.intensity_bin}`}
                tone={cell.tone}
                intensity={cell.intensity_bin}
                reward={cell.reward}
              />
            ))}
          </div>
        ) : (
          <div className="mt-2 rounded-lg border border-accent/20 bg-black/20 p-4 text-sm text-text/60">
            Пока нет данных для визуализации heatmap.
          </div>
        )}
      </div>
    </div>
  );
}
