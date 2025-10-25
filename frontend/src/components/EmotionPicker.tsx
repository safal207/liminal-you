import { useEffect, useMemo, useState } from 'react';
import { EmotionInfo, EmotionsResponse } from '../types';
import { listEmotions, suggestEmotions } from '../api/client';

type Props = {
  value: string;
  onChange: (value: string, pad?: [number, number, number]) => void;
  placeholder?: string;
};

export default function EmotionPicker({ value, onChange, placeholder }: Props) {
  const [emotions, setEmotions] = useState<EmotionsResponse | null>(null);
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<EmotionInfo[]>([]);

  useEffect(() => {
    listEmotions().then(setEmotions).catch(() => void 0);
  }, []);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setSuggestions([]);
      return;
    }
    suggestEmotions(q, 6).then(setSuggestions).catch(() => setSuggestions([]));
  }, [query]);

  const categories = useMemo(() => {
    if (!emotions) return [] as { key: string; items: EmotionInfo[] }[];
    const groups: Record<string, EmotionInfo[]> = { positive: [], negative: [], neutral: [] };
    emotions.emotions.forEach((e) => groups[e.category].push(e));
    return [
      { key: 'positive', items: groups.positive },
      { key: 'neutral', items: groups.neutral },
      { key: 'negative', items: groups.negative },
    ];
  }, [emotions]);

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onBlur={() => onChange(query)}
        placeholder={placeholder || 'Emotion'}
        className="mt-1 w-full rounded-md border border-accent/30 bg-transparent p-2 text-text focus:border-accent focus:outline-none"
      />
      {suggestions.length > 0 && (
        <ul className="mt-2 max-h-48 overflow-auto rounded-md border border-accent/30 bg-white/5 text-sm">
          {suggestions.map((s) => (
            <li
              key={s.name}
              className="cursor-pointer px-3 py-1 hover:bg-accent/20"
              onMouseDown={(e) => {
                e.preventDefault();
                setQuery(s.name);
                onChange(s.name, s.pad as [number, number, number]);
                setSuggestions([]);
              }}
            >
              {s.name}
            </li>
          ))}
        </ul>
      )}

      {!query && categories.length > 0 && (
        <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
          {categories.map((c) => (
            <div key={c.key} className="rounded-md border border-accent/20 p-2">
              <div className="mb-1 opacity-70">{c.key}</div>
              <div className="flex flex-wrap gap-1">
                {c.items.slice(0, 6).map((e) => (
                  <button
                    key={e.name}
                    className="rounded-full border border-accent/30 px-2 py-0.5 hover:bg-accent/20"
                    onClick={() => {
                      setQuery(e.name);
                      onChange(e.name, e.pad as [number, number, number]);
                    }}
                  >
                    {e.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

