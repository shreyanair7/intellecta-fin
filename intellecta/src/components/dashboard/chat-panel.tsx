import { useEffect, useRef, useState } from "react";
import { api, type Conversation, type Message } from "@/lib/api";
import { MessageBubble } from "./message-bubble";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Brain, Download, Loader2, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";

const suggestions = [
  "Summarize the key findings across all my documents.",
  "What are the main risks discussed in the uploaded reports?",
  "Compare the methodologies used in chapter 2 and 3.",
  "List the action items mentioned in my meeting notes.",
];

export function ChatPanel({
  conversation,
  onConversationChange,
}: {
  conversation: Conversation | null;
  onConversationChange: (updatedConvo?: Conversation) => void;
}) {
  const [messages, setMessages] = useState<Message[]>(conversation?.messages ?? []);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(conversation?.messages ?? []);
  }, [conversation?.id, conversation?.messages?.length]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const send = async (text: string) => {
    if (!text.trim() || sending) return;
    const convoId = conversation?.id ?? null;
    setInput("");
    setSending(true);

    const optimistic: Message = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: text.trim(),
      createdAt: Date.now(),
    };
    setMessages((m) => [...m, optimistic]);

    try {
      const res = await api.sendMessage(convoId ?? `local-${Date.now()}`, text.trim());
      setMessages(res.conversation.messages);
      onConversationChange(res.conversation);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to send");
      setMessages((m) => m.filter((x) => x.id !== optimistic.id));
    } finally {
      setSending(false);
    }
  };

  const onDownload = async () => {
    if (!conversation || messages.length === 0) {
      toast.info("Nothing to export yet.");
      return;
    }
    try {
      await api.downloadChatReport({ ...conversation, messages });
      toast.success("Chat report downloaded");
    } catch {
      toast.error("Failed to download report");
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-background">
      <header className="flex items-center justify-between gap-3 border-b border-border bg-card/50 px-4 py-3 backdrop-blur sm:px-6">
        <div className="min-w-0">
          <h2 className="truncate font-display text-base font-semibold text-foreground">
            {conversation?.title ?? "New conversation"}
          </h2>
          <p className="text-xs text-muted-foreground">
            {messages.length} message{messages.length === 1 ? "" : "s"} · Local RAG
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onDownload} className="gap-2">
          <Download className="h-4 w-4" />
          <span className="hidden sm:inline">Download Chat Report</span>
        </Button>
      </header>

      <div ref={scrollRef} className="scrollbar-thin flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        {messages.length === 0 ? (
          <EmptyState onPick={(s) => send(s)} />
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {sending && (
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-primary text-primary-foreground">
                  <Brain className="h-4 w-4" />
                </div>
                <div className="flex gap-1.5">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="border-t border-border bg-card/50 px-4 py-4 backdrop-blur sm:px-8">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-border bg-background p-2 shadow-soft focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/20"
        >
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            placeholder="Ask anything about your documents…"
            rows={1}
            className="min-h-[40px] max-h-40 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
            maxLength={2000}
          />
          <Button
            type="submit"
            disabled={sending || !input.trim()}
            className="h-10 shrink-0 bg-gradient-primary text-primary-foreground hover:opacity-95"
          >
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            <span className="ml-2 hidden sm:inline">Send</span>
          </Button>
        </form>
        <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-muted-foreground">
          Press Enter to send · Shift + Enter for newline
        </p>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (s: string) => void }) {
  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center gap-6 text-center">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-primary text-primary-foreground shadow-elegant">
        <Sparkles className="h-7 w-7" />
      </div>
      <div>
        <h3 className="font-display text-2xl font-semibold text-foreground">How can I help today?</h3>
        <p className="mt-1 text-sm text-muted-foreground">Ask a question grounded in your uploaded documents.</p>
      </div>
      <div className="grid w-full gap-2 sm:grid-cols-2">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-xl border border-border bg-card p-3 text-left text-sm text-foreground transition hover:border-primary/40 hover:shadow-soft"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
