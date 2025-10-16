import { Reflection } from '../types';

interface Props {
  reflection: Reflection;
}

export default function ReflectionCard({ reflection }: Props) {
  return (
    <article className="rounded-xl border border-accent/30 bg-white/5 p-4 shadow-lg backdrop-blur">
      <header className="flex items-center justify-between">
        <span className="text-sm uppercase tracking-widest text-accent/80">{reflection.emotion}</span>
        <span className="text-xs text-text/70">{reflection.author}</span>
      </header>
      <p className="mt-3 text-lg leading-relaxed text-text">{reflection.content}</p>
    </article>
  );
}
