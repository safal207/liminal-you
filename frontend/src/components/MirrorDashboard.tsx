import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  getMirrorPolicy,
  getMirrorStats,
  triggerMirrorReplay
} from '../api/client';
import {
  MirrorPolicyEntry,
  MirrorPolicyResponse,
  MirrorStatsResponse
} from '../types';
import { NeuroFeedbackFrame } from '../hooks/useNeuroFeedback';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';

interface MirrorDashboardProps {
  frame: NeuroFeedbackFrame | null;
  mirrorEnabled: boolean;
  onBack: () => void;
  onOpenProfile: () => void;
}

export default function MirrorDashboard({ frame, mirrorEnabled, onBack, onOpenProfile }: MirrorDashboardProps) {
  const [policy, setPolicy] = useState<MirrorPolicyResponse | null>(null);
  const [stats, setStats] = useState<MirrorStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setError(null);
    try {
      const [policyResponse, statsResponse] = await Promise.all([getMirrorPolicy(), getMirrorStats()]);
      setPolicy(policyResponse);
      setStats(statsResponse);
    } catch (err) {
      setError('Контур зеркала пока молчит — попробуй обновить позже.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const refresh = async () => {
    setRefreshing(true);
    await loadData();
  };

  const replay = async () => {
    setRefreshing(true);
    try {
      await triggerMirrorReplay();
    } catch (err) {
      setError('Не удалось перезапустить обучение — проверь соединение.');
    }
    await loadData();
  };

  const chartData = useMemo(() => {
    if (!stats?.events.length) {
      return [];
    }
    return stats.events.map((event) => ({
      ...event,
      timeLabel: new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }));
  }, [stats]);

  const heatmapEntries = useMemo(() => policy?.entries ?? [], [policy]);

  const maxPositive = useMemo(
    () => Math.max(...heatmapEntries.filter((entry) => entry.reward_avg >= 0).map((entry) => entry.reward_avg), 0.0001),
    [heatmapEntries]
  );
  const maxNegative = useMemo(
    () =>
      Math.abs(
        Math.min(...heatmapEntries.filter((entry) => entry.reward_avg < 0).map((entry) => entry.reward_avg), 0)
      ) || 0.0001,
    [heatmapEntries]
  );

  const toneOrder: Array<MirrorPolicyEntry['tone']> = ['warm', 'neutral', 'cool'];
  const intensityOrder: Array<MirrorPolicyEntry['intensity_bin']> = ['low', 'medium', 'high'];

  const bucketKey = frame?.mirror?.bucket_key ?? '–';
  const strategyLabel = frame?.mirror?.strategy === 'mirror' ? 'adaptive' : 'baseline';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-accent">Mirror Loop</h2>
          <p className="text-sm text-text/70">Самообучающийся контур резонанса</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={onBack}
            className="rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest hover:bg-accent hover:text-bg transition"
          >
            Назад
          </button>
          <button
            onClick={onOpenProfile}
            className="rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest hover:bg-accent hover:text-bg transition"
          >
            Профиль
          </button>
          <button
            onClick={refresh}
            disabled={refreshing}
            className="rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest hover:bg-accent hover:text-bg transition disabled:opacity-50"
          >
            Обновить
          </button>
          <button
            onClick={replay}
            disabled={refreshing}
            className="rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest hover:bg-accent hover:text-bg transition disabled:opacity-50"
          >
            Переобучить
          </button>
        </div>
      </div>

      {!mirrorEnabled && (
        <div className="rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-4 text-sm text-yellow-100">
          Адаптивный контур отключён в профиле — включи Mirror Loop, чтобы резонанс обучался на твоих откликах.
        </div>
      )}

      {error && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
          <div className="text-sm uppercase tracking-widest text-accent/60">Текущий bucket</div>
          <div className="mt-2 text-2xl font-semibold text-accent">{bucketKey}</div>
          <div className="mt-2 text-sm text-text/70">
            Стратегия: <span className="text-accent/80">{strategyLabel}</span>
          </div>
          <div className="mt-2 text-sm text-text/70">
            Последний тон: <span className="text-accent/80">{frame?.tone ?? '—'}</span>
          </div>
        </div>
        <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
          <div className="text-sm uppercase tracking-widest text-accent/60">Средний reward</div>
          <div className="mt-2 text-2xl font-semibold text-accent">
            {stats ? stats.avg_reward.toFixed(3) : '—'}
          </div>
          <div className="mt-2 text-sm text-text/70">
            Δ coherence: <span className="text-accent/80">{stats ? stats.avg_delta_coherence.toFixed(3) : '—'}</span>
          </div>
          <div className="mt-1 text-sm text-text/70">
            Δ entropy: <span className="text-accent/80">{stats ? stats.avg_delta_entropy.toFixed(3) : '—'}</span>
          </div>
        </div>
        <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
          <div className="text-sm uppercase tracking-widest text-accent/60">Покрытие</div>
          <div className="mt-2 text-2xl font-semibold text-accent">
            {stats ? Math.round(stats.coverage * 100) : '—'}%
          </div>
          <div className="mt-2 text-sm text-text/70">
            Bucket'ов в памяти: <span className="text-accent/80">{policy?.entries.length ?? 0}</span>
          </div>
          <div className="mt-1 text-sm text-text/70">
            Всего эпизодов: <span className="text-accent/80">{stats?.count ?? 0}</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-accent/30 bg-white/5 p-4">
          <div className="mb-4 text-sm uppercase tracking-widest text-accent/60">Δ coherence / Δ entropy</div>
          {loading ? (
            <div className="text-sm text-text/60">Загрузка временной ленты...</div>
          ) : chartData.length ? (
            <div className="h-64 w-full">
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="4 4" stroke="rgba(148, 163, 184, 0.2)" />
                  <XAxis dataKey="timeLabel" stroke="#94a3b8" tickLine={false} />
                  <YAxis stroke="#94a3b8" tickLine={false} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid rgba(148,163,184,0.3)' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="delta_coherence" stroke="#7dd3fc" strokeWidth={2} dot={false} name="Δ coherence" />
                  <Line type="monotone" dataKey="delta_entropy" stroke="#fda4af" strokeWidth={2} dot={false} name="Δ entropy" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-sm text-text/60">Пока нет достаточно событий для графика.</div>
          )}
        </div>
        <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
          <div className="mb-4 text-sm uppercase tracking-widest text-accent/60">Heatmap эффективности</div>
          <div className="space-y-2 text-sm">
            {toneOrder.map((tone) => (
              <div key={tone}>
                <div className="mb-2 text-xs uppercase tracking-widest text-accent/70">{tone}</div>
                <div className="grid grid-cols-3 gap-2">
                  {intensityOrder.map((intensity) => {
                    const entry = heatmapEntries.find(
                      (candidate) => candidate.tone === tone && candidate.intensity_bin === intensity
                    );
                    const reward = entry?.reward_avg ?? 0;
                    const color = reward >= 0
                      ? `rgba(125, 211, 252, ${0.15 + Math.min(1, reward / maxPositive) * 0.6})`
                      : `rgba(248, 113, 113, ${0.15 + Math.min(1, Math.abs(reward) / maxNegative) * 0.6})`;
                    return (
                      <div
                        key={intensity}
                        className="rounded-lg border border-accent/30 p-3 text-center"
                        style={{ background: color }}
                      >
                        <div className="text-xs uppercase tracking-widest text-text/80">{intensity}</div>
                        <div className="text-sm font-semibold text-accent">
                          {entry ? entry.reward_avg.toFixed(3) : '—'}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
        <div className="mb-4 text-sm uppercase tracking-widest text-accent/60">Журнал эпизодов</div>
        <div className="overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="text-text/60">
                <th className="px-3 py-2 font-medium">Время</th>
                <th className="px-3 py-2 font-medium">Bucket</th>
                <th className="px-3 py-2 font-medium">Тон</th>
                <th className="px-3 py-2 font-medium">Интенсивность</th>
                <th className="px-3 py-2 font-medium">Reward</th>
                <th className="px-3 py-2 font-medium">ΔCoh</th>
                <th className="px-3 py-2 font-medium">ΔEnt</th>
              </tr>
            </thead>
            <tbody>
              {stats?.events.slice(-50).reverse().map((event) => (
                <tr key={`${event.timestamp}-${event.bucket_key}`} className="border-t border-accent/20">
                  <td className="px-3 py-2 text-text/70">
                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="px-3 py-2 text-text/80">{event.bucket_key}</td>
                  <td className="px-3 py-2 text-text/80">{event.tone}</td>
                  <td className="px-3 py-2 text-text/80">{event.intensity.toFixed(2)}</td>
                  <td className="px-3 py-2 text-accent">{event.reward.toFixed(3)}</td>
                  <td className="px-3 py-2 text-accent/80">{event.delta_coherence.toFixed(3)}</td>
                  <td className="px-3 py-2 text-accent/80">{event.delta_entropy.toFixed(3)}</td>
                </tr>
              ))}
              {!stats?.events.length && (
                <tr>
                  <td colSpan={7} className="px-3 py-4 text-center text-text/60">
                    Ещё нет данных о переходах.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
