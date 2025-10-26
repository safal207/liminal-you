import { NeuroFeedbackFrame } from '../hooks/useNeuroFeedback';
import '../styles/feedback.css';

type Props = {
  frame: NeuroFeedbackFrame | null;
};

const PAD_LABELS = ['P', 'A', 'D'] as const;

export default function FeedbackAura({ frame }: Props) {
  const toneClass = frame ? `feedback-aura--${frame.tone}` : 'feedback-aura--neutral';
  const message = frame?.message ?? 'Слушаем поле.';
  const intensity = frame?.intensity ?? 0.35;

  return (
    <div className={`feedback-aura ${toneClass}`} style={{ opacity: frame ? 1 : 0 }}>
      <div className="feedback-aura__glow" style={{ opacity: 0.28 + intensity * 0.55 }} />
      <div className="feedback-aura__message">
        <p className="feedback-aura__text">{message}</p>
        {frame?.bucket_key && (
          <p className="mt-1 text-xs uppercase tracking-widest text-accent/70">
            bucket {frame.bucket_key}{frame.policy_source ? ` · ${frame.policy_source}` : ''}
          </p>
        )}
        {frame && (
          <div className="feedback-aura__metrics">
            {PAD_LABELS.map((label, index) => (
              <span key={label}>
                {label}
                <span className="feedback-aura__metric-value">{frame.pad[index].toFixed(2)}</span>
              </span>
            ))}
            <span>
              entropy
              <span className="feedback-aura__metric-value">{frame.entropy.toFixed(2)}</span>
            </span>
            <span>
              coherence
              <span className="feedback-aura__metric-value">{frame.coherence.toFixed(2)}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
