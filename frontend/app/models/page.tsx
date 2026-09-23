"use client";

import React from "react";
import AppShell from "@/app/components/AppShell";
import ModelRegistryTable from "@/app/components/ModelRegistryTable";
import RoutingRulesPanel from "@/app/components/RoutingRulesPanel";
import LiveRoutingLog from "@/app/components/LiveRoutingLog";
import ModelHealthChart from "@/app/components/ModelHealthChart";
import { useModels } from "@/app/hooks/useModels";

export default function ModelsPage() {
  const { models, rules, logs, updateRule } = useModels();

  return (
    <AppShell
      title="Model Router & Dispatcher"
      subtitle="Open-Weight Model Registry & Routing Telemetry"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Model Router" },
      ]}
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Telemetry Charts */}
        <ModelHealthChart models={models} />

        {/* Model Registry Table */}
        <ModelRegistryTable models={models} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* Routing Configuration Rules */}
          <RoutingRulesPanel rules={rules} onSaveRule={updateRule} />

          {/* Live Decision Feed */}
          <LiveRoutingLog logs={logs} />
        </div>
      </div>
    </AppShell>
  );
}
