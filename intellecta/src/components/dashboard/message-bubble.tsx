import type { Message } from "@/lib/api";
import { Brain, User as UserIcon } from "lucide-react";
import { SourcesAccordion } from "./sources-accordion";
import { cn } from "@/lib/utils";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex w-full gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-primary text-primary-foreground shadow-soft">
          <Brain className="h-4 w-4" />
        </div>
      )}
      <div className={cn("max-w-[78%] space-y-1", isUser && "items-end text-right")}>
        <div
          className={cn(
            "inline-block whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-soft",
            isUser
              ? "rounded-tr-sm bg-gradient-primary text-primary-foreground"
              : "rounded-tl-sm border border-border bg-card text-card-foreground"
          )}
        >
          {message.content}
        </div>
        {!isUser && message.sources && message.sources.length > 0 && <SourcesAccordion sources={message.sources} />}
        <p className="px-1 text-[10px] text-muted-foreground">
          {new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
      {isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
          <UserIcon className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
