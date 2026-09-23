"use client";

import React, { useState } from "react";
import AppShell from "@/app/components/AppShell";
import ChatWindow from "@/app/components/ChatWindow";

export default function ChatPage() {
  const [conversationId, setConversationId] = useState<string | null>(null);

  return (
    <AppShell
      title="Grounded Technical Chat"
      subtitle="Local KB Assistant"
      breadcrumbs={[
        { label: "Workspace", href: "/workspace" },
        { label: "Grounded Chat" },
      ]}
    >
      <div className="max-w-5xl mx-auto h-[calc(100vh-140px)] flex flex-col bg-surface border border-border rounded-2xl overflow-hidden shadow-xs">
        <ChatWindow
          conversationId={conversationId}
          type="general"
          onConversationCreated={(id) => setConversationId(id)}
        />
      </div>
    </AppShell>
  );
}
