"use client";

import { useEffect, useState } from "react";
import MermaidDiagram from "./MermaidDiagram";
import { getKnowledgeBaseGraph } from "@/app/services/api";
import type { KnowledgeBaseGraph } from "@/app/types";

export default function EquipmentGraphPanel({ className = "" }: { className?: string }) {
  const [graph, setGraph] = useState<KnowledgeBaseGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    getKnowledgeBaseGraph().then(value => { if (active) { setGraph(value); setError(null); } })
      .catch(reason => { if (active) { setGraph(null); setError(reason instanceof Error ? reason.message : "Graph unavailable"); } });
    return () => { active = false; };
  }, []);
  const chart = graph?.nodes.length ? ["graph LR", ...graph.nodes.map((node, i) => `N${i}["${node.label || node.id}"]`),
    ...graph.edges.map(edge => {
      const from = graph.nodes.findIndex(n => n.id === edge.source);
      const to = graph.nodes.findIndex(n => n.id === edge.target);
      return from >= 0 && to >= 0 ? `N${from} -->|"${edge.relationship || "connected"}"| N${to}` : "";
    }).filter(Boolean)].join("\n") : "";
  return <section className={`p-5 bg-surface border border-border rounded-2xl shadow-xs space-y-4 ${className}`}>
    <div><h3 className="font-serif font-bold text-base text-text">Equipment relationships</h3>
      <p className="text-xs text-text-3">Owner and department scoped metadata. Relationships require source verification.</p></div>
    {error && <p role="alert" className="text-sm text-red">{error}</p>}
    {graph?.nodes.length ? <>
      <div className="bg-bg-base/70 rounded-xl p-4 border border-border overflow-x-auto flex justify-center"><MermaidDiagram code={chart} /></div>
      <p className="text-xs text-text-3">{graph.nodes.length} nodes · {graph.edges.length} relationships</p>
    </> : !error && <p className="text-sm text-text-3">No equipment relationships have been added to this workspace.</p>}
  </section>;
}
