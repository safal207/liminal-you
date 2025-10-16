import { useEffect, useState } from 'react';
import { fetchProfile } from '../api/client';
import { Profile } from '../types';

interface Props {
  profileId: string;
}

export default function ProfileView({ profileId }: Props) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchProfile(profileId);
        setProfile(data);
      } catch (err) {
        setError('Профиль недоступен.');
      }
    }

    load();
  }, [profileId]);

  if (error) {
    return <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">{error}</div>;
  }

  if (!profile) {
    return <div className="rounded-xl border border-accent/30 bg-white/5 p-6 text-text/70">Загрузка профиля...</div>;
  }

  return (
    <div className="space-y-4 rounded-xl border border-accent/30 bg-white/5 p-6">
      <div>
        <h2 className="text-xl font-semibold text-accent">{profile.name}</h2>
        <p className="text-text/70">{profile.bio}</p>
      </div>
      <div>
        <h3 className="text-sm uppercase tracking-widest text-accent/80">Активные узлы</h3>
        <ul className="mt-2 space-y-2">
          {profile.nodes.map((node) => (
            <li key={node.id} className="rounded-lg border border-accent/30 px-3 py-2 text-sm text-text">
              {node.label}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="text-sm uppercase tracking-widest text-accent/80">Эмоции</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {Object.entries(profile.emotions).map(([emotion, value]) => (
            <li key={emotion} className="flex items-center justify-between">
              <span>{emotion}</span>
              <span className="text-accent">{value}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="text-sm text-text/70">Отражений: {profile.reflections_count}</div>
    </div>
  );
}
