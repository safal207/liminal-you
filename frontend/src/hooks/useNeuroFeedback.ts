import { useEffect, useRef, useState } from 'react';
import { Reflection } from '../types';

export type FeedbackTone = 'warm' | 'cool' | 'neutral';

export type CausalHint = {
  message: string;
  trend?: string;
  sourceBucket?: string;
};

export type NeuroFeedbackFrame = {
  tone: FeedbackTone;
  message: string;
  intensity: number;
  pad: [number, number, number];
  entropy: number;
  coherence: number;
  ts: number;
  samples: number;
  mirror?: {
    bucket_key?: string;
    strategy?: 'baseline' | 'mirror';
  };
  hint?: CausalHint;
};

export type FeedbackConnectionState = 'idle' | 'connecting' | 'open' | 'closed';

interface UseNeuroFeedbackOptions {
  profileId?: string;
  enabled?: boolean;
  onReflection?: (reflection: Reflection) => void;
}

interface RawFeedbackPayload {
  tone?: string;
  message?: string;
  intensity?: number;
  pad?: number[];
  entropy?: number;
  coherence?: number;
  ts?: number;
  samples?: number;
  mirror?: {
    bucket_key?: string;
    strategy?: string;
  };
  hint?: string;
  hint_meta?: {
    cause?: string;
    trend?: string;
    source_bucket?: string;
  };
}

const RETRY_DELAY = 4000;

const resolveWsUrl = (profileId?: string) => {
  const explicit = import.meta.env.VITE_API_WS_URL as string | undefined;
  const buildUrl = (base: string) => {
    const url = new URL(base);
    url.pathname = '/ws/feedback';
    if (profileId) {
      url.searchParams.set('profile_id', profileId);
    }
    return url.toString();
  };

  if (explicit) {
    try {
      return buildUrl(explicit);
    } catch (error) {
      // ignore malformed explicit urls and fall through to location-based resolution
    }
  }

  const { protocol, hostname, host } = window.location;
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';

  if (import.meta.env.DEV) {
    const backendPort = (import.meta.env.VITE_API_PORT as string | undefined) ?? '8000';
    return `${wsProtocol}//${hostname}:${backendPort}/ws/feedback${profileId ? `?profile_id=${profileId}` : ''}`;
  }

  return `${wsProtocol}//${host}/ws/feedback${profileId ? `?profile_id=${profileId}` : ''}`;
};

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

type ToneDefinition = {
  frequency: number;
  duration: number;
  type?: OscillatorType;
};

type TonePlayer = {
  play: (tone: FeedbackTone) => void;
  dispose: () => void;
};

const toneDefinitions: Record<'warm' | 'cool', ToneDefinition> = {
  warm: { frequency: 220, duration: 1.2, type: 'sine' },
  cool: { frequency: 392, duration: 1.1, type: 'triangle' }
};

const createTonePlayer = (): TonePlayer | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  const AudioContextCtor: typeof window.AudioContext | undefined =
    window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof window.AudioContext }).webkitAudioContext;

  if (!AudioContextCtor) {
    return null;
  }

  const context = new AudioContextCtor();

  const play = (tone: FeedbackTone) => {
    if (tone === 'neutral') {
      return;
    }

    const definition = toneDefinitions[tone];
    if (!definition) {
      return;
    }

    try {
      if (context.state === 'suspended') {
        void context.resume();
      }
    } catch (error) {
      // ignore resume errors – browsers may require user gestures
    }

    const now = context.currentTime;
    const oscillator = context.createOscillator();
    oscillator.type = definition.type ?? 'sine';
    oscillator.frequency.setValueAtTime(definition.frequency, now);

    const gain = context.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.18, now + 0.08);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + definition.duration);

    oscillator.connect(gain);
    gain.connect(context.destination);

    oscillator.start(now);
    oscillator.stop(now + definition.duration + 0.05);

    oscillator.onended = () => {
      oscillator.disconnect();
      gain.disconnect();
    };
  };

  const dispose = () => {
    try {
      void context.close();
    } catch (error) {
      // ignore close failures
    }
  };

  return { play, dispose };
};

export function useNeuroFeedback({ profileId, enabled = true, onReflection }: UseNeuroFeedbackOptions) {
  const [frame, setFrame] = useState<NeuroFeedbackFrame | null>(null);
  const [status, setStatus] = useState<FeedbackConnectionState>('idle');
  const reflectionHandler = useRef(onReflection);
  const toneRef = useRef<FeedbackTone | null>(null);
  const playerRef = useRef<TonePlayer | null>(null);

  useEffect(() => {
    reflectionHandler.current = onReflection;
  }, [onReflection]);

  useEffect(() => {
    playerRef.current = createTonePlayer();

    return () => {
      playerRef.current?.dispose();
      playerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!frame || typeof document === 'undefined') {
      return;
    }

    const docEl = document.documentElement;
    const [pleasure, arousal] = frame.pad;
    const breath = Math.round(3200 - clamp(arousal, 0, 1) * 1600);
    const hue = Math.round(clamp(pleasure, 0, 1) * 120);

    docEl.style.setProperty('--feedback-breath', `${breath}ms`);
    docEl.style.setProperty('--feedback-hue', `${hue}`);
    docEl.style.setProperty('--liminal-breath', `${breath}ms`);
    docEl.style.setProperty('--liminal-hue', `${hue}`);
    docEl.style.setProperty('--feedback-intensity', frame.intensity.toFixed(2));

    return () => {
      docEl.style.setProperty('--feedback-breath', '2800ms');
      docEl.style.setProperty('--feedback-hue', '90');
      docEl.style.setProperty('--liminal-breath', '2800ms');
      docEl.style.setProperty('--liminal-hue', '90');
      docEl.style.setProperty('--feedback-intensity', '0.5');
    };
  }, [frame]);

  useEffect(() => {
    if (!frame) {
      return;
    }

    if (frame.tone === toneRef.current) {
      return;
    }

    toneRef.current = frame.tone;
    if (!playerRef.current) {
      playerRef.current = createTonePlayer();
    }

    playerRef.current?.play(frame.tone);
  }, [frame]);

  useEffect(() => {
    if (!enabled) {
      setStatus('closed');
      setFrame(null);
      toneRef.current = null;
      return;
    }

    let ws: WebSocket | null = null;
    let reconnectTimeout: number | null = null;
    let shouldReconnect = true;

    const connect = () => {
      setStatus('connecting');
      const url = resolveWsUrl(profileId);
      ws = new WebSocket(url);

      ws.onopen = () => {
        setStatus('open');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as { event?: string; data?: unknown };
          if (payload.event === 'heartbeat') {
            return;
          }

          if (payload.event === 'neuro_feedback' && payload.data) {
            const candidate = payload.data as RawFeedbackPayload;
            const pad: [number, number, number] = Array.isArray(candidate.pad)
              ? ([
                  Number(candidate.pad[0] ?? 0),
                  Number(candidate.pad[1] ?? 0),
                  Number(candidate.pad[2] ?? 0)
                ] as [number, number, number])
              : [0, 0, 0];

            const tone =
              candidate.tone === 'warm' || candidate.tone === 'cool' || candidate.tone === 'neutral'
                ? (candidate.tone as FeedbackTone)
                : 'neutral';

            const mirrorInfo =
              candidate.mirror && typeof candidate.mirror === 'object'
                ? {
                    bucket_key:
                      typeof candidate.mirror.bucket_key === 'string'
                        ? candidate.mirror.bucket_key
                        : undefined,
                    strategy:
                      candidate.mirror.strategy === 'mirror' || candidate.mirror.strategy === 'baseline'
                        ? (candidate.mirror.strategy as 'mirror' | 'baseline')
                        : undefined
                  }
                : undefined;

            const bucketKey =
              mirrorInfo?.bucket_key ??
              (typeof candidate.mirror === 'object' && candidate.mirror && 'bucket_key' in candidate.mirror
                ? (candidate.mirror.bucket_key as string | undefined)
                : undefined);

            let hint: CausalHint | undefined;
            const rawHint = typeof candidate.hint === 'string' ? candidate.hint.trim() : '';
            const hintMeta =
              candidate.hint_meta && typeof candidate.hint_meta === 'object'
                ? {
                    cause:
                      typeof candidate.hint_meta.cause === 'string'
                        ? candidate.hint_meta.cause.trim()
                        : undefined,
                    trend:
                      typeof candidate.hint_meta.trend === 'string'
                        ? candidate.hint_meta.trend
                        : undefined,
                    sourceBucket:
                      typeof candidate.hint_meta.source_bucket === 'string'
                        ? candidate.hint_meta.source_bucket
                        : undefined
                  }
                : undefined;

            if (hintMeta?.cause) {
              hint = {
                message: hintMeta.cause,
                trend: hintMeta.trend,
                sourceBucket: hintMeta.sourceBucket ?? bucketKey
              };
            } else if (rawHint) {
              hint = {
                message: rawHint,
                sourceBucket: bucketKey
              };
            }

            setFrame({
              tone,
              message: typeof candidate.message === 'string' ? candidate.message : '',
              intensity: Number(candidate.intensity ?? 0),
              pad,
              entropy: Number(candidate.entropy ?? 0),
              coherence: Number(candidate.coherence ?? 0),
              ts: Number(candidate.ts ?? Date.now() / 1000),
              samples: Number(candidate.samples ?? 0),
              mirror: mirrorInfo,
              hint
            });
            return;
          }

          if (payload.event === 'new_reflection' && payload.data) {
            const candidate = payload.data as Partial<Reflection>;
            if (
              typeof candidate.id === 'string' &&
              typeof candidate.author === 'string' &&
              typeof candidate.content === 'string' &&
              typeof candidate.emotion === 'string'
            ) {
              reflectionHandler.current?.({
                id: candidate.id,
                author: candidate.author,
                content: candidate.content,
                emotion: candidate.emotion,
                pad:
                  Array.isArray(candidate.pad) && candidate.pad.length === 3
                    ? ([
                        Number(candidate.pad[0] ?? 0),
                        Number(candidate.pad[1] ?? 0),
                        Number(candidate.pad[2] ?? 0)
                      ] as [number, number, number])
                    : undefined
              });
            }
          }
        } catch (error) {
          // ignore malformed payloads to keep stream alive
        }
      };

      ws.onclose = () => {
        setStatus('closed');
        if (!shouldReconnect) {
          return;
        }
        reconnectTimeout = window.setTimeout(connect, RETRY_DELAY);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      shouldReconnect = false;
      if (reconnectTimeout) {
        window.clearTimeout(reconnectTimeout);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [enabled, profileId]);

  return { frame, status };
}
