import { useEffect, useState } from 'react';
import Feed from './components/Feed';
import ProfileView from './components/ProfileView';
import { createReflection, fetchFeed, fetchProfile } from './api/client';
import { ReflectionPayload, Reflection } from './types';

const DEFAULT_PROFILE_ID = 'user-001';

function App() {
  const [feed, setFeed] = useState<Reflection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);

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

  const handleSubmit = async (payload: ReflectionPayload) => {
    try {
      const newReflection = await createReflection(payload);
      setFeed((prev) => [newReflection, ...prev]);
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

  return (
    <div className="min-h-screen bg-bg text-text font-sans">
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
          <Feed reflections={feed} loading={loading} onSubmit={handleSubmit} />
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
