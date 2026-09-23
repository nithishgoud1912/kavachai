"use client";

import React, { use } from "react";
import AppShell from "@/app/components/AppShell";
import ChatWindow from "@/app/components/ChatWindow";

export default function ConversationDetailPage({
  params,
}: {
  params: Promise<{ conversationId: string }>;
}) {
  const { conversationId } = use(params);

  return (
    <AppShell
      title="Grounded Technical Chat"
      subtitle={`Thread ${conversationId}`}
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Chat", href: "/chat" },
        { label: conversationId },
      ]}
    >
      <div className="max-w-5xl mx-auto h-[calc(100vh-140px)] flex flex-col bg-surface border border-border rounded-2xl overflow-hidden shadow-xs">
        <ChatWindow conversationId={conversationId} type="general" />
      </div>
    </AppShell>
  );
}
