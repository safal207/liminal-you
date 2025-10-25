import { useEffect, useState } from 'react';
import { listLanguages } from '../api/client';

type Props = {
  value?: string;
  onChange?: (lang: string) => void;
};

export default function LanguageSelector({ value, onChange }: Props) {
  const [languages, setLanguages] = useState<string[]>(['ru', 'en', 'zh']);
  const [current, setCurrent] = useState<string>(value || localStorage.getItem('lang') || 'ru');

  useEffect(() => {
    listLanguages().then(setLanguages).catch(() => void 0);
  }, []);

  useEffect(() => {
    onChange?.(current);
    localStorage.setItem('lang', current);
  }, [current]);

  return (
    <select
      className="rounded-md border border-accent/40 bg-transparent px-2 py-1 text-sm"
      value={current}
      onChange={(e) => setCurrent(e.target.value)}
      aria-label="Language"
    >
      {languages.map((l) => (
        <option key={l} value={l} className="bg-[#0b0f14]">
          {l.toUpperCase()}
        </option>
      ))}
    </select>
  );
}

