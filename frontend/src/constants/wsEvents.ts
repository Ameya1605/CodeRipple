/**
 * Single source of truth for WebSocket event type strings (F-1 frontend).
 * Must match backend/core/events.py exactly.
 */
export const WS_EVENT_TYPES = {
  PROGRESS:        "progress",
  WARNING:         "warning",
  DELTA:           "delta",
  GRAPH_DATA:      "graph_data",
  CDL_DELTA:       "cdl_delta",
  RECOMMENDATIONS: "recommendations",
  COMPLETE:        "analysis_complete",
  ERROR:           "analysis_error",
  CONNECTED:       "connected",
  HEARTBEAT:       "heartbeat",
} as const;

export type WSEventType = typeof WS_EVENT_TYPES[keyof typeof WS_EVENT_TYPES];
export const TERMINAL_EVENTS = new Set([WS_EVENT_TYPES.COMPLETE, WS_EVENT_TYPES.ERROR]);
