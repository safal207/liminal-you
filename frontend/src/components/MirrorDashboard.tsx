import { useEffect, useMemo, useState } from 'react';
import { getMirrorPolicy, getMirrorStats } from '../api/client';
import { MirrorEvent, MirrorPolicyEntry, MirrorStatsPayload } from '../types';

const toneLabels: Record<string, string> = {
  warm: 'Тепло',
  cool: 'Холодок',
  neutral: 'Нейтраль'
};

function formatDelta(value: number): string {
  const rounded = value >= 0 ? `+${value.toFixed(3)}` : value.toFixed(3);
  return rounded;
}

function intensityLabel(bin: number): string {
  return (bin / 10).toFixed(1);
}

export default function MirrorDashboard() {
  const [stats, setStats] = useState<MirrorStatsPayload | null>(null);
  const [policy, setPolicy] = useState<MirrorPolicyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const [statsPayload, policyPayload] = await Promise.all([
          getMirrorStats({ limit: 200 }),
          getMirrorPolicy()
        ]);

        if (!cancelled) {
          setStats(statsPayload);
          setPolicy(policyPayload.entries);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Mirror контур пока не отвечает.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    const interval = window.setInterval(load, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const heatmap = useMemo(() => {
    const grouped: Record<string, Record<number, MirrorPolicyEntry>> = {};
    let maxReward = 0;
    policy.forEach((entry) => {
      if (!grouped[entry.tone]) {
        grouped[entry.tone] = {};
      }
      grouped[entry.tone][entry.intensity_bin] = entry;
      maxReward = Math.max(maxReward, Math.abs(entry.reward_avg));
    });
    return { grouped, maxReward: maxReward || 1 };
  }, [policy]);

  const currentContext = stats?.current;

  return (
    <div className="min-h-screen bg-black text-text">
      <header className="border-b border-accent/40 bg-black/60 px-8 py-6">
        <h1 className="text-2xl font-semibold text-accent">Mirror Loop · Resonant Learner</h1>
        <p className="mt-2 max-w-2xl text-sm text-text/70">
          Саморефлексия поля: отслеживаем пары «отклик → изменение», учимся подбирать тональность, которая усиливает
          когерентность и снижает энтропию.
        </p>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-8">
        {error && (
          <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-accent/40 bg-white/5 p-4">
            <div className="text-xs uppercase tracking-widest text-accent/70">Эпизодов</div>
            <div className="mt-2 text-3xl font-semibold text-accent">
              {stats?.summary.total_events ?? (loading ? '…' : 0)}
            </div>
            <div className="text-xs text-text/60">за последние 200 шагов</div>
          </div>
          <div className="rounded-xl border border-accent/40 bg-white/5 p-4">
            <div className="text-xs uppercase tracking-widest text-accent/70">Средний reward</div>
            <div className="mt-2 text-3xl font-semibold text-accent">
              {stats ? stats.summary.avg_reward.toFixed(3) : loading ? '…' : '0.000'}
            </div>
            <div className="text-xs text-text/60">(Δcoh − Δent)</div>
          </div>
          <div className="rounded-xl border border-accent/40 bg-white/5 p-4">
            <div className="text-xs uppercase tracking-widest text-accent/70">Покрытие bucket’ов</div>
            <div className="mt-2 text-3xl font-semibold text-accent">
              {stats ? Math.round(stats.summary.coverage * 100) : loading ? '…' : 0}%
            </div>
            <div className="text-xs text-text/60">уникальных условий за период</div>
          </div>
        </section>

        <section className="rounded-xl border border-accent/40 bg-white/5 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-accent">Δcoherence / Δentropy</h2>
            {currentContext?.bucket_key && (
              <div className="rounded-full border border-accent/50 px-3 py-1 text-xs uppercase tracking-widest text-accent/80">
                bucket {currentContext.bucket_key}{' '}
                {currentContext.policy_source ? `· ${currentContext.policy_source}` : ''}
              </div>
            )}
          </div>
          <div className="mt-4 space-y-2 text-sm">
            {(stats?.events ?? []).slice(0, 30).map((event: MirrorEvent) => (
              <div
                key={`${event.ts}-${event.tone}-${event.intensity}`}
                className="grid grid-cols-[120px_minmax(0,1fr)_100px] items-center gap-3 rounded-lg border border-accent/20 bg-black/20 px-3 py-2"
              >
                <div className="text-xs uppercase tracking-widest text-accent/70">
                  {new Date(event.ts).toLocaleTimeString()} · {toneLabels[event.tone] ?? event.tone}
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="h-2 w-full rounded-full bg-accent/10">
                      <div
                        className={`h-2 rounded-full ${event.delta_coherence >= 0 ? 'bg-emerald-400/70' : 'bg-red-400/70'}`}
                        style={{ width: `${Math.min(100, Math.abs(event.delta_coherence) * 200)}%` }}
                      />
                    </div>
                    <div className="mt-1 text-[11px] text-text/60">
                      Δcoh {formatDelta(event.delta_coherence)} / Δent {formatDelta(event.delta_entropy)}
                    </div>
                  </div>
                  <div className="text-right text-xs text-text/60">
                    {event.bucket_key}
                    <div className="text-[10px] text-text/50">{intensityLabel(event.intensity_bin)} · {event.user_count} conn</div>
                  </div>
                </div>
                <div className="text-right text-xs text-text/60">reward {event.reward.toFixed(3)}</div>
              </div>
            ))}
            {!loading && (stats?.events.length ?? 0) === 0 && (
              <div className="rounded-lg border border-accent/20 bg-black/10 p-4 text-center text-sm text-text/60">
                Пока нет зафиксированных эпизодов — подключи Mirror и подожди пару циклов.
              </div>
            )}
          </div>
        </section>

        <section className="rounded-xl border border-accent/40 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-accent">Heatmap эффективности</h2>
          <p className="mt-1 text-sm text-text/60">Тон × интенсивность (по среднему reward)</p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full table-fixed border-separate border-spacing-0 text-sm">
              <thead>
                <tr>
                  <th className="sticky left-0 bg-white/10 px-3 py-2 text-left text-xs uppercase tracking-widest text-accent/70">
                    Tone
                  </th>
                  {Array.from({ length: 11 }).map((_, index) => (
                    <th key={index} className="px-2 py-2 text-center text-xs text-text/50">
                      {intensityLabel(index)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(['warm', 'cool', 'neutral'] as const).map((tone) => (
                  <tr key={tone}>
                    <td className="sticky left-0 bg-white/10 px-3 py-2 text-xs uppercase tracking-widest text-accent/70">
                      {toneLabels[tone] ?? tone}
                    </td>
                    {Array.from({ length: 11 }).map((_, index) => {
                      const entry = heatmap.grouped[tone]?.[index];
                      const opacity = entry ? Math.min(0.9, Math.abs(entry.reward_avg) / heatmap.maxReward) : 0;
                      const color = entry && entry.reward_avg >= 0 ? 'bg-emerald-400' : 'bg-red-400';
                      return (
                        <td key={index} className="px-2 py-1 text-center text-[11px] text-text/70">
                          <div
                            className={`mx-auto h-6 w-6 rounded-full ${entry ? color : 'bg-transparent'}`}
                            style={{ opacity: entry ? 0.2 + opacity * 0.8 : 0.15 }}
                          />
                          {entry ? entry.reward_avg.toFixed(2) : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
