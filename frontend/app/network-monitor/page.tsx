"use client";

import React from "react";
import AppShell from "@/app/components/AppShell";
import EgressSummaryCard from "@/app/components/EgressSummaryCard";
import LiveConnectionFeed from "@/app/components/LiveConnectionFeed";
import AllowlistPanel from "@/app/components/AllowlistPanel";
import NetworkTopologyDiagram from "@/app/components/NetworkTopologyDiagram";
import { useNetworkMonitor } from "@/app/hooks/useNetworkMonitor";

export default function NetworkMonitorPage() {
  const { report, connections, probing, triggerProbe, reload } = useNetworkMonitor();

  return (
    <AppShell
      title="Sovereign Egress & Air-Gap Monitor"
      subtitle="Kernel Socket Auditing & Zero-Egress Air-Gap Verification"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Egress Monitor" },
      ]}
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Reassuring Big Counter Card */}
        <EgressSummaryCard
          report={report}
          onProbe={triggerProbe}
          probing={probing}
        />

        {/* Physical & Logical Topology Diagram */}
        <NetworkTopologyDiagram />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Real-time Socket Feed (7 cols) */}
          <div className="lg:col-span-7">
            <LiveConnectionFeed connections={connections} />
          </div>

          {/* Strict Allowlist Panel (5 cols) */}
          <div className="lg:col-span-5">
            <AllowlistPanel allowlist={report?.allowlist} />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
