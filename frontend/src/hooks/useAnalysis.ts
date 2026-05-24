import { useState, useEffect, useRef, useCallback } from "react";

export type AnalysisStatus = "idle" | "queued" | "running" | "complete" | "error";

export interface ProgressEvent {
  type: "progress" | "analysis_complete" | "analysis_error" | "error" | "status" | "delta" | "cdl_delta" | "recommendations" | "complete" | "graph_data";
  step?: string;
  pct?: number;
  message?: string;
  task_id?: string;
  result?: Record<string, unknown>;
  error?: string;
  text?: string;
  validation?: any;
  nodes?: any[];
  edges?: any[];
}

export interface AnalysisState {
  status: AnalysisStatus;
  taskId: string | null;
  requestId: string | null;
  progress: number;
  currentStep: string;
  result: Record<string, unknown> | null;
  error: string | null;
  streamedText: string;
  validation: any;
  graphData: { nodes: any[]; edges: any[] } | null;
}

const API_BASE = "";
const WS_BASE = window.location.protocol === 'https:' ? 'wss://' + window.location.host : 'ws://' + window.location.host;
const DEV_TOKEN = import.meta.env.VITE_DEV_TOKEN ?? "dev-local-token";

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({
    status: "idle",
    taskId: null,
    requestId: null,
    progress: 0,
    currentStep: "Ready",
    result: null,
    error: null,
    streamedText: "",
    validation: null,
    graphData: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const stateRef = useRef(state);
  useEffect(() => { stateRef.current = state; }, [state]);

  const reconnectCountRef = useRef(0);
  const MAX_RECONNECTS = 3;
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const connectWebSocket = useCallback((taskId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    const wsUrl = `${WS_BASE}/ws/analyze/${taskId}?token=${DEV_TOKEN}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS] Connected to task ${taskId}`);
      reconnectCountRef.current = 0; // Reset on successful connect
      
      // Setup heartbeat ping
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "heartbeat" }));
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      let parsed: ProgressEvent;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        console.error("[WS] Invalid JSON from server:", event.data);
        return;
      }

      if (parsed.type === "progress" || parsed.type === "status") {
        setState(prev => ({
          ...prev,
          status: "running",
          progress: parsed.pct ?? prev.progress,
          currentStep: parsed.message ?? parsed.step ?? prev.currentStep,
        }));
      } else if (parsed.type === "delta") {
        setState(prev => ({
          ...prev,
          status: "running",
          streamedText: prev.streamedText + (parsed.text || ""),
        }));
      } else if (parsed.type === "graph_data") {
        setState(prev => ({
          ...prev,
          graphData: { nodes: parsed.nodes ?? [], edges: parsed.edges ?? [] }
        }));
      } else if (parsed.type === "complete" || parsed.type === "analysis_complete") {
        setState(prev => ({
          ...prev,
          status: "complete",
          progress: 100,
          result: parsed.result ?? null,
          validation: parsed.validation ?? null,
          currentStep: "Complete",
        }));
        ws.close(1000);
      } else if (parsed.type === "analysis_error" || parsed.type === "error") {
        setState(prev => ({
          ...prev,
          status: "error",
          error: parsed.error ?? parsed.message ?? "Unknown error",
        }));
        ws.close(1011);
      }
    };

    ws.onerror = (event) => {
      console.error("[WS] Error:", event);
    };

    ws.onclose = (event) => {
      console.log(`[WS] Closed. Code: ${event.code}, Clean: ${event.wasClean}`);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      wsRef.current = null;
      
      // Don't reconnect on successful completion or explicit error close
      if (event.code === 1000 || event.code === 1011) return;

      if (!event.wasClean && stateRef.current.status === "running") {
        if (reconnectCountRef.current < MAX_RECONNECTS) {
          reconnectCountRef.current += 1;
          const delay = Math.pow(2, reconnectCountRef.current) * 1000;
          setState(prev => ({ ...prev, currentStep: `Reconnecting (Attempt ${reconnectCountRef.current})...` }));
          setTimeout(() => connectWebSocket(taskId), delay);
        } else {
          setState(prev => ({ ...prev, status: "error", error: "Connection lost during analysis (Max retries exceeded)" }));
        }
      }
    };
  }, []);

  const triggerAnalysis = useCallback(async (payload: any) => {
    reconnectCountRef.current = 0;
    setState({ status: "queued", taskId: null, requestId: null, progress: 0, currentStep: "Queuing...", result: null, error: null, streamedText: "", validation: null, graphData: null });

    try {
      const res = await fetch(`${API_BASE}/api/v1/analyze/symbol`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${DEV_TOKEN}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`Dispatch failed: ${res.status} — ${detail}`);
      }

      const { task_id, request_id } = await res.json();

      setState(prev => ({ ...prev, taskId: task_id, requestId: request_id, currentStep: "Connecting..." }));

      connectWebSocket(task_id);

    } catch (err) {
      setState(prev => ({
        ...prev,
        status: "error",
        error: err instanceof Error ? err.message : String(err),
      }));
    }
  }, [connectWebSocket]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { state, triggerAnalysis };
}
