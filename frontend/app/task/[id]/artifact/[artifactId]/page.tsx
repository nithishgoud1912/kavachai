"use client";

import React, { use } from "react";
import Link from "next/link";
import AppShell from "@/app/components/AppShell";
import DocxPreview from "@/app/components/DocxPreview";
import PptxPreview from "@/app/components/PptxPreview";
import XlsxPreview from "@/app/components/XlsxPreview";
import CodeViewer from "@/app/components/CodeViewer";
import AnnotatedImage from "@/app/components/AnnotatedImage";
import { useTask } from "@/app/hooks/useTask";

export default function ArtifactViewerPage({
  params,
}: {
  params: Promise<{ id: string; artifactId: string }>;
}) {
  const { id, artifactId } = use(params);
  const { task, loading } = useTask(id);

  if (loading) {
    return (
      <AppShell title="Artifact Viewer">
        <div className="flex h-96 items-center justify-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      </AppShell>
    );
  }

  // Find artifact in task
  const artifact = task?.artifacts.find((a) => a.id === artifactId) || task?.artifacts[0];

  if (!artifact) {
    return (
      <AppShell title="Artifact Viewer">
        <div className="max-w-xl mx-auto p-8 bg-surface border border-border rounded-2xl text-center space-y-4 my-12">
          <span className="text-3xl">📁</span>
          <h3 className="font-serif text-lg font-bold text-text">Artifact Not Found</h3>
          <p className="text-xs text-text-3">The requested deliverable was not found in task {id}.</p>
          <Link
            href={`/task/${id}`}
            className="inline-block px-4 py-2 rounded-xl bg-accent text-white text-xs font-semibold"
          >
            Back to Task
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={artifact.name}
      subtitle="Full Deliverable Preview"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: `Task ${id}`, href: `/task/${id}` },
        { label: artifact.name },
      ]}
    >
      <div className="space-y-6 pb-12">
        {artifact.type === "docx" && <DocxPreview artifact={artifact} />}
        {artifact.type === "pptx" && <PptxPreview artifact={artifact} />}
        {artifact.type === "xlsx" && <XlsxPreview artifact={artifact} />}
        {artifact.type === "code" && <CodeViewer artifact={artifact} />}
        {artifact.type === "image" && (
          <AnnotatedImage
            imageUrl={artifact.preview_url || "/api/placeholder/800/500"}
            alt={artifact.name}
            modelUsed={artifact.model_used}
          />
        )}
      </div>
    </AppShell>
  );
}
