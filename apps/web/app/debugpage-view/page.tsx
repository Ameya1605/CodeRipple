import { useState, useEffect } from "react";

export function DebugPage() {
  const [brokerStatus, setBrokerStatus] = useState<"checking" | "ok" | "error">("checking");
  const [wsStatus, setWsStatus] = useState<"idle" | "connected" | "error">("idle");
  const [events, setEvents] = useState<string[]>([]);

  useEffect(() => {
    fetch("/api/v1/analyze/health")
      .then(r => r.json())
      .then(d => setBrokerStatus(d.broker_connected ? "ok" : "error"))
      .catch(() => setBrokerStatus("error"));
  }, []);

  const testWebSocket = () => {
    const ws = new WebSocket(`${import.meta.env.VITE_API_URL?.replace("http", "ws") || "ws://localhost:8000"}/ws/analyze/test-task?token=${import.meta.env.VITE_DEV_TOKEN || "dev-local-token"}`);
    ws.onopen = () => setWsStatus("connected");
    ws.onerror = () => setWsStatus("error");
    ws.onmessage = (e) => setEvents(prev => [...prev.slice(-19), e.data]);
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "monospace" }}>
      <h2>Connection Debugger</h2>
      <p>Broker: <strong>{brokerStatus}</strong></p>
      <p>WebSocket: <strong>{wsStatus}</strong></p>
      <button onClick={testWebSocket}>Test WebSocket</button>
      <pre>{events.join("\n")}</pre>
    </div>
  );
}
