"use client";

import type { AgentName, AgentStatus, SubTask } from "@/app/types";
import { ALL_AGENTS } from "@/app/types";
import AgentRow from "./AgentRow";

interface AgentState {
  status: AgentStatus;
  message: string;
  elapsed_ms: number;
}

interface AgentTimelineProps {
  agents: Record<AgentName, AgentState>;
  plan?: SubTask[];
}

export default function AgentTimeline({ agents, plan }: AgentTimelineProps) {
  const planGoals = plan
    ? Object.fromEntries(plan.map((t) => [t.agent, t.goal]))
    : {};

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-border">
        <h3 className="text-sm font-medium text-text-2">Agent Activity</h3>
      </div>
      <div className="divide-y divide-border/50">
        {ALL_AGENTS.map((agent, i) => (
          <AgentRow
            key={agent}
            agent={agent}
            status={agents[agent].status}
            message={agents[agent].message}
            elapsed_ms={agents[agent].elapsed_ms}
            goal={planGoals[agent]}
            index={i}
          />
        ))}
      </div>
    </div>
  );
}
