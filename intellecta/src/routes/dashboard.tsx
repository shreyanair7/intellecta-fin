import { createFileRoute, Navigate } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, type Conversation, type UploadedDoc } from "@/lib/api";
import { Sidebar } from "@/components/dashboard/sidebar";
import { TopBar } from "@/components/dashboard/top-bar";
import { ChatPanel } from "@/components/dashboard/chat-panel";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Intellecta" }, { name: "description", content: "Chat with your knowledge base." }] }),
  component: DashboardPage,
});

function DashboardPage() {
  const { user, loading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<UploadedDoc[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  // Active conversation object (kept in state for instant re-render after send)
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const refreshConvos = useCallback(async () => {
    if (!user) return;
    try {
      const list = await api.listConversationsAsync();
      setConversations(list);
    } catch { /* backend not yet running */ }
  }, [user]);

  const refreshDocs = useCallback(async () => {
    if (!user) return;
    try {
      const list = await api.listDocumentsAsync();
      setDocuments(list);
    } catch { /* backend not yet running */ }
  }, [user]);

  useEffect(() => {
    if (!user) return;
    refreshConvos();
    refreshDocs();
  }, [user, refreshConvos, refreshDocs]);

  // Load active conversation when activeId changes
  useEffect(() => {
    if (!activeId) { setActiveConversation(null); return; }
    if (activeId.startsWith("local-")) return; // local draft
    api.getConversationAsync(activeId).then((c) => setActiveConversation(c));
  }, [activeId]);

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-background text-muted-foreground">Loading…</div>;
  if (!user) return <Navigate to="/login" />;

  const handleConversationChange = async (updatedConvo?: Conversation) => {
    if (updatedConvo) {
      setActiveConversation(updatedConvo);
      setActiveId(updatedConvo.id);
    }
    await refreshConvos();
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => { setActiveId(id); setSidebarOpen(false); }}
        onNewChat={() => { setActiveId(null); setActiveConversation(null); setSidebarOpen(false); }}
        onConversationsChange={async () => {
          await refreshConvos();
          if (activeId) {
            const still = conversations.find((c) => c.id === activeId);
            if (!still) { setActiveId(null); setActiveConversation(null); }
          }
        }}
        documents={documents}
        onDocumentsChange={refreshDocs}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setSidebarOpen(true)} />
        <ChatPanel
          conversation={activeConversation}
          onConversationChange={handleConversationChange}
        />
      </div>
    </div>
  );
}
