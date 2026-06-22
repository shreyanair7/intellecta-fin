import { api, type Conversation, type UploadedDoc } from "@/lib/api";
import { Brain, MessageSquarePlus, Trash2, MessagesSquare, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FileUploader } from "./file-uploader";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export function Sidebar({
  open,
  onClose,
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onConversationsChange,
  documents,
  onDocumentsChange,
}: {
  open: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onConversationsChange: () => void;
  documents: UploadedDoc[];
  onDocumentsChange: () => void;
}) {
  return (
    <>
      {open && <div onClick={onClose} className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm lg:hidden" />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-sidebar text-sidebar-foreground transition-transform lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2 font-display text-lg font-semibold">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary text-primary-foreground">
              <Brain className="h-4 w-4" />
            </span>
            Intellecta
          </div>
          <button onClick={onClose} className="rounded-md p-1 text-sidebar-foreground/70 hover:bg-sidebar-accent lg:hidden" aria-label="Close sidebar">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-3">
          <Button onClick={onNewChat} className="w-full justify-start gap-2 bg-sidebar-accent text-sidebar-foreground hover:bg-sidebar-accent/80">
            <MessageSquarePlus className="h-4 w-4" />
            New chat
          </Button>
        </div>

        <div className="scrollbar-thin mt-4 flex-1 overflow-y-auto px-3">
          <SectionLabel icon={<MessagesSquare className="h-3 w-3" />}>Conversations</SectionLabel>
          {conversations.length === 0 ? (
            <p className="px-2 py-1 text-[11px] text-sidebar-foreground/50">No chats yet.</p>
          ) : (
            <ul className="space-y-0.5">
              {conversations.map((c) => (
                <li key={c.id}>
                  <button
                    onClick={() => onSelect(c.id)}
                    className={cn(
                      "group flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-sm text-sidebar-foreground/85 transition hover:bg-sidebar-accent",
                      activeId === c.id && "bg-sidebar-accent text-sidebar-foreground"
                    )}
                  >
                    <span className="flex-1 truncate">{c.title}</span>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          await api.deleteConversation(c.id);
                          toast.success("Conversation deleted");
                          onConversationsChange();
                        } catch {
                          toast.error("Failed to delete conversation");
                        }
                      }}
                      className="rounded p-1 text-sidebar-foreground/40 opacity-0 transition group-hover:opacity-100 hover:bg-destructive/30 hover:text-destructive-foreground"
                      aria-label={`Delete ${c.title}`}
                    >
                      <Trash2 className="h-3 w-3" />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="mt-6">
            <SectionLabel>Knowledge base</SectionLabel>
            <FileUploader documents={documents} onChange={onDocumentsChange} />
          </div>
        </div>

        <div className="border-t border-sidebar-border p-3 text-[11px] text-sidebar-foreground/50">
          Local RAG · v0.1 preview
        </div>
      </aside>
    </>
  );
}

function SectionLabel({ children, icon }: { children: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <div className="mb-2 flex items-center gap-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
      {icon}{children}
    </div>
  );
}
