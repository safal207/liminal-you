import { CSSProperties, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Reflection } from '../types';

interface Props {
  reflection: Reflection;
  highlighted?: boolean;
}

const accentPalette: Record<string, string> = {
  радость: 'rgba(255, 238, 88, 0.35)',
  спокойствие: 'rgba(111, 255, 233, 0.4)',
  вдохновение: 'rgba(139, 233, 255, 0.45)',
  любовь: 'rgba(255, 153, 204, 0.4)',
  грусть: 'rgba(138, 180, 248, 0.35)',
};

const containerVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

export default function ReflectionCard({ reflection, highlighted = false }: Props) {
  const pulseColor = useMemo(() => {
    const key = reflection.emotion.toLowerCase();
    return accentPalette[key] ?? 'rgba(111, 255, 233, 0.35)';
  }, [reflection.emotion]);

  const highlightStyles: CSSProperties | undefined = highlighted
    ? ({ '--pulse-color': pulseColor } as CSSProperties)
    : undefined;

  return (
    <motion.article
      className={`group relative overflow-hidden rounded-xl border border-accent/30 bg-white/5 p-4 shadow-lg backdrop-blur transition-shadow ${highlighted ? 'resonance-flash' : ''}`}
      style={highlightStyles}
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-0 transition-opacity duration-700 group-hover:opacity-80" style={{ background: `radial-gradient(circle at top, ${pulseColor}, transparent 65%)` }} />
      <header className="flex items-center justify-between">
        <span className="text-sm uppercase tracking-widest text-accent/80">{reflection.emotion}</span>
        <span className="text-xs text-text/70">{reflection.author}</span>
      </header>
      <p className="mt-3 text-lg leading-relaxed text-text">{reflection.content}</p>
    </motion.article>
  );
}
