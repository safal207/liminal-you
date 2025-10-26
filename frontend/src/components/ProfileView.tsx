import { useEffect, useState } from 'react';
import {
  fetchProfile,
  updateAstroPreference,
  updateFeedbackPreference,
  updateMirrorPreference
} from '../api/client';
import { Profile } from '../types';

interface Props {
  profileId: string;
  initialProfile?: Profile | null;
  onProfileUpdate?: (profile: Profile) => void;
}

export default function ProfileView({ profileId, initialProfile = null, onProfileUpdate }: Props) {
  const [profile, setProfile] = useState<Profile | null>(initialProfile);
  const [error, setError] = useState<string | null>(null);
  const [updatingAstro, setUpdatingAstro] = useState(false);
  const [updatingFeedback, setUpdatingFeedback] = useState(false);
  const [updatingMirror, setUpdatingMirror] = useState(false);

  useEffect(() => {
    setProfile(initialProfile);
  }, [initialProfile]);

  useEffect(() => {
    if (initialProfile) {
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        const data = await fetchProfile(profileId);
        if (!cancelled) {
          setProfile(data);
          onProfileUpdate?.(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Профиль недоступен.');
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [initialProfile, onProfileUpdate, profileId]);

  if (error) {
    return <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">{error}</div>;
  }

  if (!profile) {
    return <div className="rounded-xl border border-accent/30 bg-white/5 p-6 text-text/70">Загрузка профиля...</div>;
  }

  const toggleAstroPreference = async () => {
    setUpdatingAstro(true);
    try {
      const updated = await updateAstroPreference(profile.id, !profile.astro_opt_out);
      setProfile(updated);
      onProfileUpdate?.(updated);
    } catch (err) {
      setError('Не удалось обновить настройку AstroLayer.');
    } finally {
      setUpdatingAstro(false);
    }
  };

  const toggleFeedbackPreference = async () => {
    setUpdatingFeedback(true);
    try {
      const updated = await updateFeedbackSettings(
        profile.id,
        !profile.feedback_enabled,
        profile.mirror_enabled
      );
      setProfile(updated);
      onProfileUpdate?.(updated);
    } catch (err) {
      setError('Не удалось обновить контур обратной связи.');
    } finally {
      setUpdatingFeedback(false);
    }
  };

  const toggleMirrorPreference = async () => {
    setUpdatingMirror(true);
    try {
      const updated = await updateMirrorPreference(profile.id, !profile.mirror_enabled);
      setProfile(updated);
      onProfileUpdate?.(updated);
    } catch (err) {
      setError('Не получилось настроить адаптивный резонанс.');
    } finally {
      setUpdatingMirror(false);
    }
  };

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
      <div className="flex items-center justify-between rounded-lg border border-accent/30 bg-black/20 p-3 text-sm">
        <div>
          <div className="font-medium text-accent">AstroLayer</div>
          <p className="text-text/60">Не вплетать мои эмоции в общее поле</p>
        </div>
        <button
          onClick={toggleAstroPreference}
          disabled={updatingAstro}
          className={`relative inline-flex h-7 w-12 items-center rounded-full border transition ${
            profile.astro_opt_out ? 'border-accent bg-accent/40' : 'border-accent/50 bg-black/40'
          } ${updatingAstro ? 'opacity-60' : 'hover:border-accent'}`}
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-accent transition ${
              profile.astro_opt_out ? 'translate-x-5' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
      <div className="flex items-center justify-between rounded-lg border border-accent/30 bg-black/20 p-3 text-sm">
        <div>
          <div className="font-medium text-accent">Feedback Aura</div>
          <p className="text-text/60">Нежные подсказки из общего поля</p>
        </div>
        <button
          onClick={toggleFeedbackPreference}
          disabled={updatingFeedback}
          className={`relative inline-flex h-7 w-12 items-center rounded-full border transition ${
            profile.feedback_enabled ? 'border-accent bg-accent/40' : 'border-accent/50 bg-black/40'
          } ${updatingFeedback ? 'opacity-60' : 'hover:border-accent'}`}
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-accent transition ${
              profile.feedback_enabled ? 'translate-x-5' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
      <div className="flex items-center justify-between rounded-lg border border-accent/30 bg-black/20 p-3 text-sm">
        <div>
          <div className="font-medium text-accent">Mirror Loop</div>
          <p className="text-text/60">Адаптивный резонанс по отпечаткам поля</p>
        </div>
        <button
          onClick={toggleMirrorPreference}
          disabled={updatingMirror}
          className={`relative inline-flex h-7 w-12 items-center rounded-full border transition ${
            profile.mirror_enabled ? 'border-accent bg-accent/40' : 'border-accent/50 bg-black/40'
          } ${updatingMirror ? 'opacity-60' : 'hover:border-accent'}`}
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-accent transition ${
              profile.mirror_enabled ? 'translate-x-5' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
    </div>
  );
}
