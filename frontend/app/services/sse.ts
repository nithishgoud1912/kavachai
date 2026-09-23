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

// ─── Sovereign Workbench Task SSE Stream ────────────────────────────

import type { SubTaskItem, ToolCallEvent, ArtifactItem, EvidenceReference } from "@/app/types";

export interface TaskSSEHandlers {
  onPlanCreated?: (plan: SubTaskItem[]) => void;
  onSubtaskStarted?: (data: { subtask_id: string; model?: string }) => void;
  onSubtaskCompleted?: (data: { subtask_id: string; duration_ms?: number }) => void;
  onSubtaskFailed?: (data: { subtask_id: string; error: string }) => void;
  onToolCallStarted?: (data: ToolCallEvent) => void;
  onToolCallResult?: (data: ToolCallEvent) => void;
  onModelSelected?: (data: { task_type: string; model: string; reason?: string }) => void;
  onOutputDelta?: (delta: string) => void;
  onArtifactCreated?: (artifact: ArtifactItem) => void;
  onCitationAdded?: (citation: EvidenceReference) => void;
  onHitlRequired?: (data: { task_id: string; prompt?: string }) => void;
  onTaskCompleted?: (data: { task_id: string; duration_ms?: number }) => void;
  onTaskFailed?: (data: { task_id: string; error: string }) => void;
  onError?: (error: Event) => void;
  onReconnecting?: () => void;
}

export function connectToTaskStream(
  taskId: string,
  handlers: TaskSSEHandlers
): SSEConnection {
  const url = `/api/v1/tasks/${taskId}/stream`;
  const seenEventIds = new Set<string>();
  let eventSource: EventSource | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  let closed = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (closed) return;
    eventSource = new EventSource(url);

    const bind = (eventName: string, callback?: (parsed: any) => void) => {
      if (!callback) return;
      eventSource?.addEventListener(eventName, (e: MessageEvent) => {
        const id = e.lastEventId || `${eventName}_${e.data}`;
        if (seenEventIds.has(id)) return;
        seenEventIds.add(id);
        try {
          const parsed = JSON.parse(e.data);
          callback(parsed);
        } catch {
          callback(e.data);
        }
      });
    };

    bind("plan_created", handlers.onPlanCreated);
    bind("subtask_started", handlers.onSubtaskStarted);
    bind("subtask_completed", handlers.onSubtaskCompleted);
    bind("subtask_failed", handlers.onSubtaskFailed);
    bind("tool_call_started", handlers.onToolCallStarted);
    bind("tool_call_result", handlers.onToolCallResult);
    bind("model_selected", handlers.onModelSelected);
    bind("output_delta", (data) => handlers.onOutputDelta?.(typeof data === "string" ? data : data?.delta || ""));
    bind("artifact_created", handlers.onArtifactCreated);
    bind("citation_added", handlers.onCitationAdded);
    bind("hitl_required", handlers.onHitlRequired);
    bind("task_completed", (data) => {
      handlers.onTaskCompleted?.(data);
      cleanup();
    });
    bind("task_failed", (data) => {
      handlers.onTaskFailed?.(data);
      cleanup();
    });

    eventSource.onerror = (error: Event) => {
      if (closed) return;
      handlers.onError?.(error);
      eventSource?.close();
      eventSource = null;
      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000);
        handlers.onReconnecting?.();
        reconnectTimer = setTimeout(connect, delay);
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

