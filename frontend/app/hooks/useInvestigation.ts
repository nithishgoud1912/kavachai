"use client";

import { useState, useCallback } from "react";
import type {
  AgentName,
  AgentStatus,
  AgentUpdate,
  InvestigationState,
  Report,
  ALL_AGENTS,
} from "@/app/types";

interface AgentState {
  status: AgentStatus;
  message: string;
  elapsed_ms: number;
}

interface InvestigationHookState {
  investigationState: InvestigationState;
  investigationId: string | null;
  agents: Record<AgentName, AgentState>;
  report: Report | null;
  insufficientMessage: string | null;
  error: string | null;
}

interface InvestigationHookActions {
  setCreating: () => void;
  setStreaming: (investigationId: string) => void;
  updateAgent: (update: AgentUpdate) => void;
  setCompleted: (report: Report) => void;
  setInsufficientEvidence: (message: string) => void;
  setFailed: (error: string) => void;
  setRecovering: () => void;
  reset: () => void;
}

const INITIAL_AGENT_STATE: AgentState = {
  status: "pending",
  message: "",
  elapsed_ms: 0,
};

function createInitialAgents(): Record<AgentName, AgentState> {
  return {
    planner: { ...INITIAL_AGENT_STATE },
    document_agent: { ...INITIAL_AGENT_STATE },
    data_agent: { ...INITIAL_AGENT_STATE },
    vision_agent: { ...INITIAL_AGENT_STATE },
    rag_agent: { ...INITIAL_AGENT_STATE },
    verification_agent: { ...INITIAL_AGENT_STATE },
  };
}

export function useInvestigation(): InvestigationHookState & InvestigationHookActions {
  const [state, setState] = useState<InvestigationHookState>({
    investigationState: "idle",
    investigationId: null,
    agents: createInitialAgents(),
    report: null,
    insufficientMessage: null,
    error: null,
  });

  const setCreating = useCallback(() => {
    setState({
      investigationState: "creating",
      investigationId: null,
      agents: createInitialAgents(),
      report: null,
      insufficientMessage: null,
      error: null,
    });
  }, []);

  const setStreaming = useCallback((investigationId: string) => {
    setState((prev) => ({
      ...prev,
      investigationState: "streaming",
      investigationId,
    }));
  }, []);

  const updateAgent = useCallback((update: AgentUpdate) => {
    setState((prev) => ({
      ...prev,
      agents: {
        ...prev.agents,
        [update.agent]: {
          status: update.status,
          message: update.message,
          elapsed_ms: update.elapsed_ms,
        },
      },
    }));
  }, []);

  const setCompleted = useCallback((report: Report) => {
    setState((prev) => ({
      ...prev,
      investigationState: "completed",
      report,
    }));
  }, []);

  const setInsufficientEvidence = useCallback((message: string) => {
    setState((prev) => ({
      ...prev,
      investigationState: "insufficient_evidence",
      insufficientMessage: message,
    }));
  }, []);

  const setFailed = useCallback((error: string) => {
    setState((prev) => ({
      ...prev,
      investigationState: "failed",
      error,
    }));
  }, []);

  const setRecovering = useCallback(() => {
    setState((prev) => ({
      ...prev,
      investigationState: "recovering",
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      investigationState: "idle",
      investigationId: null,
      agents: createInitialAgents(),
      report: null,
      insufficientMessage: null,
      error: null,
    });
  }, []);

  return {
    ...state,
    setCreating,
    setStreaming,
    updateAgent,
    setCompleted,
    setInsufficientEvidence,
    setFailed,
    setRecovering,
    reset,
  };
}
