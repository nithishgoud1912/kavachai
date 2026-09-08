import type { AgentUpdate, SSEInvestigationComplete, SSEInsufficientEvidence } from "@/app/types";
import { getStreamUrl } from "./api";

export interface SSEHandlers {
  onAgentUpdate: (update: AgentUpdate) => void;
  onInvestigationComplete: (data: SSEInvestigationComplete) => void;
  onInsufficientEvidence: (data: SSEInsufficientEvidence) => void;
  onError?: (error: Event) => void;
  onReconnecting?: () => void;
}

interface SSEConnection {
  close: () => void;
}

export function connectToInvestigationStream(
  investigationId: string,
  handlers: SSEHandlers
): SSEConnection {
  const url = getStreamUrl(investigationId);
  const seenEventIds = new Set<string>();
  let eventSource: EventSource | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  let closed = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (closed) return;

    eventSource = new EventSource(url);

    eventSource.addEventListener("agent_update", (event: MessageEvent) => {
      // Duplicate protection
      const eventId = event.lastEventId || `agent_update_${event.data}`;
      if (seenEventIds.has(eventId)) return;
      seenEventIds.add(eventId);

      try {
        const data: AgentUpdate = JSON.parse(event.data);
        handlers.onAgentUpdate(data);
      } catch (e) {
        console.error("[KavachAI SSE] Failed to parse agent_update:", e);
      }
    });

    eventSource.addEventListener("investigation_complete", (event: MessageEvent) => {
      const eventId = event.lastEventId || `complete_${event.data}`;
      if (seenEventIds.has(eventId)) return;
      seenEventIds.add(eventId);

      try {
        const data: SSEInvestigationComplete = JSON.parse(event.data);
        handlers.onInvestigationComplete(data);
        cleanup(); // Terminal event — stop listening
      } catch (e) {
        console.error("[KavachAI SSE] Failed to parse investigation_complete:", e);
      }
    });

    eventSource.addEventListener("insufficient_evidence", (event: MessageEvent) => {
      const eventId = event.lastEventId || `insufficient_${event.data}`;
      if (seenEventIds.has(eventId)) return;
      seenEventIds.add(eventId);

      try {
        const data: SSEInsufficientEvidence = JSON.parse(event.data);
        handlers.onInsufficientEvidence(data);
        cleanup(); // Terminal event — stop listening
      } catch (e) {
        console.error("[KavachAI SSE] Failed to parse insufficient_evidence:", e);
      }
    });

    eventSource.onerror = (error: Event) => {
      if (closed) return;

      handlers.onError?.(error);

      // Close current connection
      eventSource?.close();
      eventSource = null;

      // Attempt reconnect with exponential backoff
      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000);

        handlers.onReconnecting?.();

        reconnectTimer = setTimeout(() => {
          connect();
        }, delay);
      }
    };

    eventSource.onopen = () => {
      reconnectAttempts = 0;
    };
  }

  function cleanup() {
    closed = true;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  connect();

  return { close: cleanup };
}
