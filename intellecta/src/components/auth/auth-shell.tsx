import { Link } from "@tanstack/react-router";
import { Brain } from "lucide-react";
import type { ReactNode } from "react";

export function AuthShell({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden bg-gradient-hero text-white lg:flex lg:flex-col lg:justify-between lg:p-12">
        <Link to="/" className="flex items-center gap-2 font-display text-xl font-semibold">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-white/15 backdrop-blur">
            <Brain className="h-5 w-5" />
          </span>
          Intellecta
        </Link>
        <div className="relative space-y-6">
          <div className="absolute -left-10 top-0 h-64 w-64 rounded-full bg-primary-glow/30 blur-3xl" />
          <h2 className="relative font-display text-4xl font-semibold leading-tight">
            Your private knowledge,<br /> instantly conversational.
          </h2>
          <p className="relative max-w-md text-white/70">
            Intellecta indexes your documents on-device and gives you cited, source-grounded answers. No data leaves your stack.
          </p>
          <ul className="relative space-y-2 text-sm text-white/80">
            <li>• Local RAG — your files stay yours</li>
            <li>• Inline citations with page-level snippets</li>
            <li>• Multi-document upload, drag &amp; drop</li>
            <li>• Export full chat reports</li>
          </ul>
        </div>
        <p className="text-xs text-white/50">© {new Date().getFullYear()} Intellecta. All rights reserved.</p>
      </div>

      <div className="flex items-center justify-center px-6 py-12 sm:px-12">
        <div className="w-full max-w-sm">
          <Link to="/" className="mb-8 flex items-center gap-2 font-display text-xl font-semibold lg:hidden">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-primary text-primary-foreground">
              <Brain className="h-5 w-5" />
            </span>
            Intellecta
          </Link>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">{title}</h1>
          <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-8">{children}</div>
          <div className="mt-6 text-sm text-muted-foreground">{footer}</div>
        </div>
      </div>
    </div>
  );
}
