import { useState } from "react";
import type { Source } from "@/lib/api";
import { ChevronDown, FileText, Quote } from "lucide-react";
import { cn } from "@/lib/utils";

export function SourcesAccordion({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-border/70 bg-background/50">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-xs font-medium text-muted-foreground transition hover:bg-muted"
        aria-expanded={open}
      >
        <span className="inline-flex items-center gap-2">
          <Quote className="h-3.5 w-3.5" />
          {sources.length} source{sources.length === 1 ? "" : "s"} cited
        </span>
        <ChevronDown className={cn("h-4 w-4 transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <ul className="divide-y divide-border/70 border-t border-border/70">
          {sources.map((s, i) => (
            <li key={s.id} className="space-y-1.5 p-3">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                <span className="grid h-5 w-5 place-items-center rounded-md bg-primary/10 text-[10px] font-semibold text-primary">{i + 1}</span>
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="truncate">{s.documentName}</span>
                <span className="ml-auto text-xs text-muted-foreground">p. {s.page}</span>
              </div>
              <p className="border-l-2 border-primary/30 pl-3 text-xs leading-relaxed text-muted-foreground">{s.snippet}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
