import { useState, useEffect, useCallback, useRef } from 'react';

export function useWebSocket(url: string | null) {
  const [messages, setMessages] = useState<any[]>([]);
  const [status, setStatus] = useState<'DISCONNECTED' | 'CONNECTING' | 'CONNECTED'>('DISCONNECTED');
  const ws = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!url) return;
    setStatus('CONNECTING');
    setMessages([]);
    const socket = new WebSocket(url);
    
    socket.onopen = () => setStatus('CONNECTED');
    socket.onclose = () => setStatus('DISCONNECTED');
    socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setMessages(prev => [...prev, data]);
      } catch (err) {
        console.error("Failed to parse WS message", err);
      }
    };
    
    ws.current = socket;
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return { messages, status };
}
