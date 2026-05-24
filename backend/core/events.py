"""
Single source of truth for all WebSocket event type strings.
Import from here everywhere — never use raw string literals for event types.
"""


class WSEventType:
    # Progress events
    PROGRESS         = "progress"
    WARNING          = "warning"
    DELTA            = "delta"
    GRAPH_DATA       = "graph_data"
    CDL_DELTA        = "cdl_delta"
    RECOMMENDATIONS  = "recommendations"

    # Terminal events — WebSocket MUST close after receiving these
    COMPLETE         = "analysis_complete"
    ERROR            = "analysis_error"

    # System events
    CONNECTED        = "connected"
    HEARTBEAT        = "heartbeat"


TERMINAL_EVENTS = {WSEventType.COMPLETE, WSEventType.ERROR}
