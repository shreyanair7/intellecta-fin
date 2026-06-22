import { useCallback, useRef, useState } from "react";
import { api, type UploadedDoc } from "@/lib/api";
import { File, Loader2, Trash2, Upload } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const formatBytes = (b: number) => {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
};

export function FileUploader({ documents, onChange }: { documents: UploadedDoc[]; onChange: () => void }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState<{ name: string; pct: number } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      for (const f of list) {
        if (f.size > 20 * 1024 * 1024) {
          toast.error(`${f.name} exceeds 20 MB`);
          continue;
        }
        setUploading({ name: f.name, pct: 0 });
        try {
          await api.uploadDocument(f, (pct) => setUploading({ name: f.name, pct }));
          toast.success(`Uploaded ${f.name}`);
          onChange();
        } catch (e) {
          toast.error(e instanceof Error ? e.message : `Failed to upload ${f.name}`);
        }
      }
      setUploading(null);
    },
    [onChange]
  );

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "group cursor-pointer rounded-xl border-2 border-dashed p-4 text-center transition",
          dragging ? "border-sidebar-primary bg-sidebar-accent" : "border-sidebar-border hover:border-sidebar-primary/60 hover:bg-sidebar-accent/50"
        )}
        role="button"
        tabIndex={0}
      >
        <Upload className="mx-auto h-5 w-5 text-sidebar-foreground/70 transition group-hover:text-sidebar-primary" />
        <p className="mt-2 text-xs font-medium text-sidebar-foreground">Drag &amp; drop files</p>
        <p className="text-[11px] text-sidebar-foreground/60">or click to browse · PDF, DOCX, MD, TXT</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.md,.txt,.docx"
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {uploading && (
        <div className="rounded-lg bg-sidebar-accent/60 p-2.5">
          <div className="mb-1.5 flex items-center gap-2 text-xs text-sidebar-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span className="flex-1 truncate">{uploading.name}</span>
            <span className="text-sidebar-foreground/70">{uploading.pct}%</span>
          </div>
          <Progress value={uploading.pct} className="h-1.5 bg-sidebar-border" />
        </div>
      )}

      {documents.length > 0 ? (
        <ul className="space-y-1.5">
          {documents.map((d) => (
            <li
              key={d.id}
              className="group flex items-center gap-2 rounded-lg bg-sidebar-accent/40 px-2.5 py-2 text-xs text-sidebar-foreground hover:bg-sidebar-accent"
            >
              <File className="h-3.5 w-3.5 shrink-0 text-sidebar-primary" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{d.name}</p>
                <p className="text-[10px] text-sidebar-foreground/60">{formatBytes(d.size)}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 transition group-hover:opacity-100 hover:bg-destructive/20 hover:text-destructive"
                onClick={async (e) => {
                  e.stopPropagation();
                  try {
                    await api.deleteDocument(d.id);
                    toast.success("Removed document");
                    onChange();
                  } catch {
                    toast.error("Failed to remove document");
                  }
                }}
                aria-label={`Delete ${d.name}`}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-center text-[11px] text-sidebar-foreground/50">No documents indexed yet.</p>
      )}
    </div>
  );
}
