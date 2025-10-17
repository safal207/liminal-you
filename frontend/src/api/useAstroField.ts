import { useEffect, useRef } from 'react';

export type AstroFieldState = {
  field_id: string;
  pad_avg: [number, number, number];
  entropy: number;
  coherence: number;
  ts: number;
  samples: number;
};

type AstroHandler = (state: AstroFieldState) => void;

const HEARTBEAT_MS = 20000;
const RETRY_DELAY = 3000;

const resolveAstroUrl = () => {
  const explicit = import.meta.env.VITE_API_WS_URL;
  if (explicit) {
    return String(explicit).replace(/\/ws\/resonance$/, '/ws/astro');
  }

  const { protocol, hostname, host } = window.location;
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';

  if (import.meta.env.DEV) {
    const backendPort = (import.meta.env.VITE_API_PORT as string | undefined) ?? '8000';
    return `${wsProtocol}//${hostname}:${backendPort}/ws/astro`;
  }

  return `${wsProtocol}//${host}/ws/astro`;
};

export function useAstroField(onField: AstroHandler) {
  const handlerRef = useRef(onField);
  const reconnectTimeout = useRef<number | null>(null);
  const heartbeatRef = useRef<number | null>(null);

  useEffect(() => {
    handlerRef.current = onField;
  }, [onField]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let mounted = true;

    const teardown = () => {
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
    };

    const connect = () => {
      const url = resolveAstroUrl();
      ws = new WebSocket(url);

      ws.onopen = () => {
        ws?.send('astro-online');
        teardown();
        heartbeatRef.current = window.setInterval(() => {
          try {
            ws?.send('astro-pulse');
          } catch (error) {
            // Ignore send failures, socket will reconnect on close.
          }
        }, HEARTBEAT_MS);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as { event?: string; data?: unknown };
          if (payload?.event === 'astro_field' && payload.data) {
            const candidate = payload.data as Partial<AstroFieldState>;
            if (
              candidate &&
              Array.isArray(candidate.pad_avg) &&
              candidate.pad_avg.length === 3 &&
              typeof candidate.entropy === 'number' &&
              typeof candidate.coherence === 'number' &&
              typeof candidate.ts === 'number' &&
              typeof candidate.samples === 'number'
            ) {
              handlerRef.current({
                field_id: candidate.field_id ?? 'global',
                pad_avg: [
                  Number(candidate.pad_avg[0] ?? 0),
                  Number(candidate.pad_avg[1] ?? 0),
                  Number(candidate.pad_avg[2] ?? 0)
                ],
                entropy: Number(candidate.entropy),
                coherence: Number(candidate.coherence),
                ts: Number(candidate.ts),
                samples: Number(candidate.samples)
              });
            }
          }
        } catch (error) {
          // Ignore malformed payloads silently.
        }
      };

      ws.onclose = () => {
        teardown();
        if (!mounted) {
          return;
        }
        reconnectTimeout.current = window.setTimeout(connect, RETRY_DELAY);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      mounted = false;
      teardown();
      if (reconnectTimeout.current) {
        window.clearTimeout(reconnectTimeout.current);
      }
      ws?.close();
    };
  }, []);
}
