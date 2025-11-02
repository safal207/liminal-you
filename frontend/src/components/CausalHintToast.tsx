import { useEffect } from 'react';
import { CausalHint } from '../hooks/useNeuroFeedback';

type Props = {
  hint: CausalHint;
  visible: boolean;
  onClose?: () => void;
  duration?: number;
};

export default function CausalHintToast({ hint, visible, onClose, duration = 6000 }: Props) {
  useEffect(() => {
    if (!visible) {
      return;
    }

    if (!duration) {
      return;
    }

    const timer = window.setTimeout(() => {
      onClose?.();
    }, duration);

    return () => window.clearTimeout(timer);
  }, [visible, duration, onClose]);

  if (!visible) {
    return null;
  }

  return (
    <div className="pointer-events-auto">
      <div className="rounded-2xl border border-accent/40 bg-white/10 px-5 py-4 shadow-xl backdrop-blur">
        <div className="text-xs uppercase tracking-widest text-accent/60">Причина отклика</div>
        <div className="mt-1 text-sm font-medium text-accent">{hint.message}</div>
        {(hint.trend || hint.sourceBucket) && (
          <div className="mt-1 text-xs text-text/70">
            {hint.trend && <span className="mr-2">{hint.trend}</span>}
            {hint.sourceBucket && <span>bucket {hint.sourceBucket}</span>}
          </div>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="mt-3 rounded-full border border-accent/50 px-3 py-1 text-xs uppercase tracking-widest text-accent hover:bg-accent hover:text-bg transition"
          >
            ok
          </button>
        )}
      </div>
    </div>
  );
}
