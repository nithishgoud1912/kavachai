"use client";

import React, { useState } from "react";
import type { RoutingRule } from "@/app/types";
import { getModelDisplayName } from "@/app/utils/modelNames";

interface RoutingRulesPanelProps {
  rules: RoutingRule[];
  onSaveRule?: (rule: RoutingRule) => Promise<unknown> | unknown;
  className?: string;
}

export default function RoutingRulesPanel({
  rules,
  onSaveRule,
  className = "",
}: RoutingRulesPanelProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRule, setNewRule] = useState<Partial<RoutingRule>>({
    task_type: "",
    preferred_model_id: "qwen2.5:3b",
    condition_description: "",
    enabled: true,
  });

  const handleCreate = async () => {
    if (!newRule.task_type || !newRule.preferred_model_id) return;
    const rule: RoutingRule = {
      id: `rule-${Date.now()}`,
      task_type: newRule.task_type,
      preferred_model_id: newRule.preferred_model_id,
      condition_description: newRule.condition_description || "Custom task dispatch rule",
      enabled: true,
    };
    await onSaveRule?.(rule);
    setShowAddModal(false);
    setNewRule({ task_type: "", preferred_model_id: "qwen2.5:3b", condition_description: "", enabled: true });
  };

  return (
    <div className={`bg-surface border border-border rounded-2xl p-5 shadow-xs space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
        <div>
          <h3 className="font-serif font-bold text-base text-text">Model Auto-Routing Rules</h3>
          <p className="text-xs text-text-3 font-mono">
            Deterministic Task Intent → On-Premise Specialized LLM Engine Mapping
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-3 py-1.5 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-xs transition-colors cursor-pointer"
        >
          + Add Routing Rule
        </button>
      </div>

      <div className="space-y-3">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="p-3.5 rounded-xl border border-border bg-bg-base/50 hover:bg-surface transition-colors flex items-center justify-between gap-4"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-text">{rule.task_type}</span>
                <span className="text-[10px] text-text-3 font-mono">→</span>
                <span className="font-mono text-xs font-bold text-accent bg-accent/10 px-2 py-0.5 rounded">
                  {getModelDisplayName(rule.preferred_model_id)}
                </span>
                {rule.fallback_model_id && (
                  <span className="text-[10px] text-text-3 font-mono">
                    (fallback: {getModelDisplayName(rule.fallback_model_id)})
                  </span>
                )}
              </div>
              <p className="text-xs text-text-2">{rule.condition_description}</p>
            </div>

            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green" />
              <span className="text-xs font-mono text-green font-medium">Active</span>
            </div>
          </div>
        ))}
      </div>

      {showAddModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-border rounded-2xl p-6 max-w-md w-full shadow-xl space-y-4">
            <h4 className="font-serif font-bold text-base text-text">Register New Routing Rule</h4>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-text-2 mb-1">Task Category / Intent</label>
                <input
                  type="text"
                  placeholder="e.g. Hazardous Area Classification / ATEX"
                  value={newRule.task_type}
                  onChange={(e) => setNewRule({ ...newRule, task_type: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block font-semibold text-text-2 mb-1">Preferred Local Model</label>
                <select
                  value={newRule.preferred_model_id}
                  onChange={(e) => setNewRule({ ...newRule, preferred_model_id: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent font-mono"
                >
                  <option value="qwen2.5:3b">Reasoning model</option>
                  <option value="qwen2.5-coder:3b">coder model (engineering calculations with steps)</option>
                  <option value="qwen2.5vl:3b">vision language model</option>
                  <option value="codellama:7b">codellama:7b (Python AST)</option>
                  <option value="nomic-embed-text">Embedding model</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-text-2 mb-1">Routing Condition Description</label>
                <input
                  type="text"
                  placeholder="Triggered when queries reference ATEX zones or explosion safety standards"
                  value={newRule.condition_description}
                  onChange={(e) => setNewRule({ ...newRule, condition_description: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-border bg-bg-base focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-3 py-1.5 rounded-lg border border-border text-xs text-text hover:bg-surface-2 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-1.5 rounded-lg bg-accent text-white hover:bg-accent-hover text-xs font-semibold transition-colors cursor-pointer"
              >
                Save Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
