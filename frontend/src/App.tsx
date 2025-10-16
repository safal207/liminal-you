import { useCallback, useEffect, useRef, useState } from 'react';
import Feed from './components/Feed';
import ProfileView from './components/ProfileView';
import { createReflection, fetchFeed, fetchProfile } from './api/client';
import { useResonanceSocket } from './api/useResonanceSocket';
import { ReflectionPayload, Reflection } from './types';

const DEFAULT_PROFILE_ID = 'user-001';
const HIGHLIGHT_DURATION = 2400;

function App() {
  const [feed, setFeed] = useState<Reflection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [highlightedIds, setHighlightedIds] = useState<string[]>([]);
  const highlightTimers = useRef<Record<string, number>>({});
  const audioContextRef = useRef<AudioContext | null>(null);

  const ensureAudioContext = useCallback(async (): Promise<AudioContext | null> => {
    if (typeof window === 'undefined') {
      return null;
    }

    const globalWindow = window as Window & { webkitAudioContext?: typeof AudioContext };
    const AudioContextCtor = window.AudioContext ?? globalWindow.webkitAudioContext;

    if (!AudioContextCtor) {
      return null;
    }

    let context = audioContextRef.current;

    if (!context || context.state === 'closed') {
      context = new AudioContextCtor();
      audioContextRef.current = context;
    }

    if (context.state === 'suspended') {
      try {
        await context.resume();
      } catch (error) {
        return null;
      }
    }

    return context;
  }, []);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchFeed();
        setFeed(data);
      } catch (err) {
        setError('Не удалось загрузить ленту.');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const handleUserGesture = () => {
      void ensureAudioContext();
    };

    window.addEventListener('pointerdown', handleUserGesture, { once: true });

    return () => {
      window.removeEventListener('pointerdown', handleUserGesture);
    };
  }, [ensureAudioContext]);

  useEffect(() => {
    return () => {
      Object.values(highlightTimers.current).forEach((timer) => window.clearTimeout(timer));
      highlightTimers.current = {};

      const context = audioContextRef.current;
      audioContextRef.current = null;

      if (context && context.state !== 'closed') {
        void context.close().catch(() => {});
      }
    };
  }, []);

  const playResonance = useCallback(() => {
    ensureAudioContext()
      .then((context) => {
        if (!context) {
          return;
        }

        const oscillator = context.createOscillator();
        const gain = context.createGain();
        const now = context.currentTime;

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(432, now);

        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(0.02, now + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);

        oscillator.connect(gain);
        gain.connect(context.destination);

        oscillator.onended = () => {
          oscillator.disconnect();
          gain.disconnect();
        };

        oscillator.start(now);
        oscillator.stop(now + 0.6);
      })
      .catch(() => {
        // Ignore playback failures silently to avoid interrupting the flow.
      });
  }, [ensureAudioContext]);

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
      setError('Не удалось отправить отражение.');
    }
  };

  const toggleProfile = async () => {
    if (!profileOpen) {
      try {
        await fetchProfile(DEFAULT_PROFILE_ID);
        setProfileOpen(true);
      } catch (err) {
        setError('Профиль недоступен.');
      }
    } else {
      setProfileOpen(false);
    }
  };

  const handleResonanceMessage = useCallback(
    (message: { event: string; data?: unknown }) => {
      if (message.event !== 'new_reflection' || !message.data) {
        return;
      }

      const payload = message.data as Record<string, unknown>;
      const candidate: Reflection | null =
        typeof payload.id === 'string' &&
        typeof payload.author === 'string' &&
        typeof payload.content === 'string' &&
        typeof payload.emotion === 'string'
          ? {
              id: payload.id,
              author: payload.author,
              content: payload.content,
              emotion: payload.emotion,
            }
          : null;

      if (!candidate) {
        return;
      }

      setFeed((prev) => {
        const exists = prev.some((item) => item.id === candidate.id);
        if (exists) {
          return prev;
        }
        return [candidate, ...prev];
      });

      registerHighlight(candidate.id);
      playResonance();
    },
    [playResonance, registerHighlight]
  );

  useResonanceSocket(handleResonanceMessage);

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg text-text font-sans">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-[-15%] h-[80%] w-[120%] -translate-x-1/2 rounded-full bg-gradient-to-b from-accent/20 via-accent/10 to-transparent blur-3xl opacity-60 animate-breath" />
        <div className="absolute inset-x-0 bottom-[-30%] h-1/2 bg-gradient-to-t from-accent/10 via-transparent to-transparent blur-3xl animate-breath" />
      </div>
      <header className="border-b border-accent/40 p-6 flex justify-between items-center">
        <h1 className="text-2xl font-semibold tracking-wide text-accent">Liminal-You</h1>
        <button
          onClick={toggleProfile}
          className="rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest hover:bg-accent hover:text-bg transition"
        >
          {profileOpen ? 'Закрыть профиль' : 'Профиль'}
        </button>
      </header>
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
            <ProfileView profileId={DEFAULT_PROFILE_ID} />
          </aside>
        )}
      </main>
    </div>
  );
}

export default App;
