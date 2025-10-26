import { useCallback, useEffect, useRef, useState } from 'react';
import Feed from './components/Feed';
import ProfileView from './components/ProfileView';
import FeedbackAura from './components/FeedbackAura';
import LoginForm from './components/LoginForm';
import LanguageSelector from './components/LanguageSelector';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import DeviceInfo from './components/DeviceInfo';
import MirrorDashboard from './components/MirrorDashboard';
import { createReflection, fetchFeed, fetchProfile } from './api/client';
import { ReflectionPayload, Reflection, Profile } from './types';
import { useNeuroFeedback } from './hooks/useNeuroFeedback';
import { useAstroField, AstroFieldState } from './hooks/useAstroField';

const DEFAULT_PROFILE_ID = 'user-001';
const HIGHLIGHT_DURATION = 2400;

function App() {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/';
  if (path.startsWith('/mirror')) {
    return <MirrorDashboard />;
  }

  const [feed, setFeed] = useState<Reflection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [highlightedIds, setHighlightedIds] = useState<string[]>([]);
  const [fieldState, setFieldState] = useState<AstroFieldState | null>(null);
  const [overload, setOverload] = useState(false);
  const [submissionsRate, setSubmissionsRate] = useState(0);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [feedbackEnabled, setFeedbackEnabled] = useState(true);
  const highlightTimers = useRef<Record<string, number>>({});
  const astroLastSample = useRef<{ ts: number; samples: number } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchFeed();
        setFeed(data);
      } catch (err) {
        setError('Не удалось загрузить ленту — поле пока молчит.');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      try {
        const data = await fetchProfile(DEFAULT_PROFILE_ID);
        if (!cancelled) {
          setProfile(data);
          setFeedbackEnabled(data.feedback_enabled);
        }
      } catch (err) {
        if (!cancelled) {
          setFeedbackEnabled(true);
        }
      }
    }

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  const registerHighlight = useCallback((id: string) => {
    setHighlightedIds((prev) => (prev.includes(id) ? prev : [id, ...prev]));

    if (highlightTimers.current[id]) {
      window.clearTimeout(highlightTimers.current[id]);
    }

    highlightTimers.current[id] = window.setTimeout(() => {
      setHighlightedIds((prev) => prev.filter((existing) => existing !== id));
      delete highlightTimers.current[id];
    }, HIGHLIGHT_DURATION);
  }, []);

  const handleSubmit = async (payload: ReflectionPayload) => {
    try {
      await createReflection(payload);
    } catch (err) {
      setError('Не получилось записать отражение. Попробуй ещё раз.');
    }
  };

  const toggleProfile = async () => {
    if (!profileOpen) {
      if (!profile) {
        try {
          const data = await fetchProfile(DEFAULT_PROFILE_ID);
          setProfile(data);
          setFeedbackEnabled(data.feedback_enabled);
        } catch (err) {
          setError('Профиль не отвечает — попробуем чуть позже.');
          return;
        }
      }
      setProfileOpen(true);
    } else {
      setProfileOpen(false);
    }
  };

  const handleReflectionEvent = useCallback(
    (reflection: Reflection) => {
      setFeed((prev) => {
        const exists = prev.some((item) => item.id === reflection.id);
        if (exists) {
          return prev;
        }
        return [reflection, ...prev];
      });

      registerHighlight(reflection.id);
    },
    [registerHighlight]
  );

  const handleFieldUpdate = useCallback((state: AstroFieldState) => {
    setFieldState(state);

    const previous = astroLastSample.current;
    let rate = 0;
    if (previous && state.ts > previous.ts && state.samples >= previous.samples) {
      const deltaSamples = state.samples - previous.samples;
      const deltaSeconds = Math.max(1, state.ts - previous.ts);
      rate = (deltaSamples / deltaSeconds) * 60;
    }

    astroLastSample.current = { ts: state.ts, samples: state.samples };
    setSubmissionsRate(rate);

    const overloadThreshold = 6;
    setOverload(state.entropy > 0.7 && rate > overloadThreshold);
  }, []);

  const { frame: feedbackFrame } = useNeuroFeedback({
    profileId: DEFAULT_PROFILE_ID,
    enabled: feedbackEnabled,
    onReflection: handleReflectionEvent
  });

  useAstroField(feedbackFrame, handleFieldUpdate);

  useEffect(() => {
    if (typeof document === 'undefined') {
      return;
    }

    const docEl = document.documentElement;
    docEl.style.setProperty('--liminal-intensity', (fieldState?.coherence ?? 0.5).toFixed(2));

    return () => {
      docEl.style.setProperty('--liminal-intensity', '0.5');
    };
  }, [fieldState]);

  useEffect(() => {
    return () => {
      Object.values(highlightTimers.current).forEach((timer) => window.clearTimeout(timer));
      highlightTimers.current = {};
    };
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-field text-text font-sans body-breath">
      <FeedbackAura frame={feedbackFrame} />
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="astro-breath absolute left-1/2 top-[-15%] h-[80%] w-[120%] -translate-x-1/2 rounded-full bg-gradient-to-b from-accent/30 via-accent/10 to-transparent blur-3xl opacity-70" />
        <div className="astro-breath absolute inset-x-0 bottom-[-30%] h-1/2 bg-gradient-to-t from-accent/10 via-transparent to-transparent blur-3xl" />
      </div>
      <header className="border-b border-accent/40 p-6 flex justify-between items-center">
        <h1 className="text-2xl font-semibold tracking-wide text-accent">Liminal-You</h1>
        <button
          onClick={toggleProfile}
          className="rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest hover:bg-accent hover:text-bg transition"
        >
          {profileOpen ? 'Скрыть профиль' : 'Открыть профиль'}
        </button>
      </header>
      <div className="flex items-center justify-end gap-3 px-6 py-3 border-b border-accent/20">
        <LanguageSelector />
        <LoginForm onLogin={() => void 0} />
      </div>
      {overload && (
        <div className="mx-6 mt-4 rounded-xl border border-yellow-400/60 bg-yellow-400/10 p-4 text-sm text-yellow-100">
          Поле перенасыщено (энтропия {fieldState?.entropy.toFixed(2)}). Скорость отражений {submissionsRate.toFixed(1)} в минуту — дай системе вдох.
        </div>
      )}
      {error && <div className="bg-red-500/20 border border-red-500/40 text-red-200 p-4 m-6 rounded">{error}</div>}
      <main className="grid gap-8 p-6 md:grid-cols-[2fr_1fr]">
        <section>
          <Feed
            reflections={feed}
            loading={loading}
            onSubmit={handleSubmit}
            highlightedIds={highlightedIds}
          />
        </section>
        {profileOpen && (
          <aside>
            <ProfileView
              profileId={DEFAULT_PROFILE_ID}
              initialProfile={profile}
              onProfileUpdate={(updated) => {
                setProfile(updated);
                setFeedbackEnabled(updated.feedback_enabled);
              }}
            />
          </aside>
        )}
      </main>
      <div className="grid gap-4 p-6 md:grid-cols-[2fr_1fr]">
        <div></div>
        <div className="space-y-4">
          <AnalyticsDashboard />
          <DeviceInfo />
        </div>
      </div>
    </div>
  );
}

export default App;
