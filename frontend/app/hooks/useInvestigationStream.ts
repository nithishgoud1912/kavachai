"use client";

import { useEffect, useRef } from "react";
import { connectToInvestigationStream } from "@/app/services/sse";
import type { AgentUpdate, SSEInvestigationComplete, SSEInsufficientEvidence } from "@/app/types";

interface StreamHandlers {
  onAgentUpdate: (update: AgentUpdate) => void;
  onInvestigationComplete: (data: SSEInvestigationComplete) => void;
  onInsufficientEvidence: (data: SSEInsufficientEvidence) => void;
  onError?: (error: Event) => void;
  onReconnecting?: () => void;
}

export function useInvestigationStream(
  investigationId: string | null,
  handlers: StreamHandlers
) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  useEffect(() => {
    if (!investigationId) return;

    const connection = connectToInvestigationStream(investigationId, {
      onAgentUpdate: (update) => handlersRef.current.onAgentUpdate(update),
      onInvestigationComplete: (data) => handlersRef.current.onInvestigationComplete(data),
      onInsufficientEvidence: (data) => handlersRef.current.onInsufficientEvidence(data),
      onError: (error) => handlersRef.current.onError?.(error),
      onReconnecting: () => handlersRef.current.onReconnecting?.(),
    });

    return () => {
      connection.close();
    };
  }, [investigationId]);
}
