import { FormEvent, useState } from 'react';
import ReflectionCard from './ReflectionCard';
import { Reflection, ReflectionPayload } from '../types';

interface Props {
  reflections: Reflection[];
  loading: boolean;
  onSubmit: (payload: ReflectionPayload) => Promise<void>;
}

const defaultForm: ReflectionPayload = {
  from_node: 'node-alpha',
  to_user: 'user-001',
  message: '',
  emotion: 'свет'
};

export default function Feed({ reflections, loading, onSubmit }: Props) {
  const [form, setForm] = useState<ReflectionPayload>(defaultForm);
  const [sending, setSending] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSending(true);
    await onSubmit(form);
    setForm({ ...defaultForm, message: '' });
    setSending(false);
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="rounded-xl border border-accent/30 bg-white/5 p-6">
        <h2 className="text-xl font-semibold text-accent">Отразить</h2>
        <div className="mt-4 space-y-4">
          <label className="block">
            <span className="text-sm text-text/70">Эмоция</span>
            <input
              className="mt-1 w-full rounded-md border border-accent/30 bg-transparent p-2 text-text focus:border-accent focus:outline-none"
              value={form.emotion}
              onChange={(e) => setForm({ ...form, emotion: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-text/70">Сообщение</span>
            <textarea
              className="mt-1 w-full rounded-md border border-accent/30 bg-transparent p-2 text-text focus:border-accent focus:outline-none"
              rows={3}
              value={form.message}
              onChange={(e) => setForm({ ...form, message: e.target.value })}
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={sending || form.message.trim() === ''}
          className="mt-4 rounded-full border border-accent px-4 py-2 text-sm uppercase tracking-widest text-accent transition hover:bg-accent hover:text-bg disabled:opacity-50"
        >
          {sending ? 'Отправка...' : 'Отправить отражение'}
        </button>
      </form>

      <div className="space-y-4">
        {loading ? (
          <p className="text-text/70">Загрузка резонансов...</p>
        ) : reflections.length === 0 ? (
          <p className="text-text/70">Пока тихо. Оставь первое отражение.</p>
        ) : (
          reflections.map((reflection) => <ReflectionCard key={reflection.id} reflection={reflection} />)
        )}
      </div>
    </div>
  );
}
