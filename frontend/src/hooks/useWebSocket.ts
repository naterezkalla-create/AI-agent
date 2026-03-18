import { useCallback, useRef, useState } from 'react';
import type { WSEvent } from '../types';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // Connect directly to backend to avoid Vite proxy issues
    const ws = new WebSocket('ws://localhost:8000/ws/chat');
    console.log('[WS] Connecting to ws://localhost:8000/ws/chat');

    ws.onopen = () => {
      console.log('[WS] Connected');
      setConnected(true);
    };
    ws.onclose = () => {
      console.log('[WS] Disconnected');
      setConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();

    wsRef.current = ws;
  }, []);

  const sendMessage = useCallback(
    (message: string, conversationId?: string, onEvent?: (event: WSEvent) => void) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        return;
      }

      ws.onmessage = (e) => {
        console.log('[WS] Received:', e.data);
        const event: WSEvent = JSON.parse(e.data);
        onEvent?.(event);
      };

      ws.send(
        JSON.stringify({
          message,
          conversation_id: conversationId,
        })
      );
    },
    []
  );

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { connect, sendMessage, disconnect, connected };
}
