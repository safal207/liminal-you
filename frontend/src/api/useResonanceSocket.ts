import { useEffect, useRef } from 'react';

type ResonanceMessage = {
  event: string;
  [key: string]: unknown;
};

type MessageHandler = (message: ResonanceMessage) => void;

const DEFAULT_RETRY_DELAY = 2000;

const resolveWsUrl = () => {
  const explicit = import.meta.env.VITE_API_WS_URL;
  if (explicit) {
    return explicit as string;
  }

  const { protocol, hostname, host } = window.location;
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';

  if (import.meta.env.DEV) {
    const backendPort = (import.meta.env.VITE_API_PORT as string | undefined) ?? '8000';
    return `${wsProtocol}//${hostname}:${backendPort}/ws/resonance`;
  }

  return `${wsProtocol}//${host}/ws/resonance`;
};

export function useResonanceSocket(onMessage: MessageHandler) {
  const handlerRef = useRef(onMessage);
  const reconnectTimeout = useRef<number | null>(null);

  useEffect(() => {
    handlerRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let mounted = true;

    const connect = () => {
      const url = resolveWsUrl();
      ws = new WebSocket(url);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handlerRef.current(data);
        } catch (error) {
          // Ignore malformed payloads silently to keep the flow.
        }
      };

      ws.onclose = () => {
        if (!mounted) {
          return;
        }
        reconnectTimeout.current = window.setTimeout(connect, DEFAULT_RETRY_DELAY);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      mounted = false;
      if (reconnectTimeout.current) {
        window.clearTimeout(reconnectTimeout.current);
      }
      ws?.close();
    };
  }, []);
}
