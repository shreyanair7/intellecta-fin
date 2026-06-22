/**
 * Intellecta API layer — wired to FastAPI backend at localhost:8000.
 * Falls back gracefully when the backend is unreachable.
 */

const BASE_URL = "http://localhost:8000/api/v1";

export type User = { id: string; name: string; email: string };
export type Source = { id: string; documentName: string; page: number; snippet: string };
export type Message = {
  id: string;
  role: "user" | "ai";
  content: string;
  createdAt: number;
  sources?: Source[];
};
export type Conversation = {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
};
export type UploadedDoc = {
  id: string;
  name: string;
  size: number;
  uploadedAt: number;
};

// ─── Token storage ────────────────────────────────────────────────────────────
const TOKEN_KEY = "intellecta.jwt";
const USER_KEY = "intellecta.user";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
function storeUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// ─── HTTP helpers ─────────────────────────────────────────────────────────────
function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...authHeaders(),
    ...extraHeaders,
  };
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ─── Response normalizers (camelCase dates) ───────────────────────────────────
function normalizeMessage(m: any): Message {
  return {
    id: m.id,
    role: m.role,
    content: m.content,
    createdAt: new Date(m.createdAt).getTime(),
    sources: m.sources ?? undefined,
  };
}

function normalizeConversation(c: any): Conversation {
  return {
    id: c.id,
    title: c.title,
    updatedAt: new Date(c.updatedAt).getTime(),
    messages: (c.messages ?? []).map(normalizeMessage),
  };
}

function normalizeDoc(d: any): UploadedDoc {
  return {
    id: d.id,
    name: d.name,
    size: d.size,
    uploadedAt: new Date(d.uploadedAt).getTime(),
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────
export const api = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  async signUp(name: string, email: string, password: string): Promise<User> {
    const res = await request<{ access_token: string; user: User }>("POST", "/auth/register", {
      name,
      email,
      password,
    });
    setToken(res.access_token);
    storeUser(res.user);
    return res.user;
  },

  async logIn(email: string, password: string): Promise<User> {
    const res = await request<{ access_token: string; user: User }>("POST", "/auth/login", {
      email,
      password,
    });
    setToken(res.access_token);
    storeUser(res.user);
    return res.user;
  },

  logOut() {
    clearSession();
  },

  getSession(): (User & { token: string }) | null {
    const token = getToken();
    const user = getStoredUser();
    if (!token || !user) return null;
    return { ...user, token };
  },

  // ── Conversations ─────────────────────────────────────────────────────────
  async listConversationsAsync(): Promise<Conversation[]> {
    const data = await request<any[]>("GET", "/chat/conversations");
    return data.map(normalizeConversation);
  },

  listConversations(): Conversation[] {
    // Synchronous stub used by dashboard — real data comes via useEffect
    return [];
  },

  async getConversationAsync(id: string): Promise<Conversation | null> {
    try {
      const data = await request<any>("GET", `/chat/conversations/${id}`);
      return normalizeConversation(data);
    } catch {
      return null;
    }
  },

  getConversation(id: string): Conversation | null {
    // Sync stub — real data loaded async in dashboard
    return null;
  },

  async createConversationAsync(): Promise<Conversation> {
    const data = await request<any>("POST", "/chat/conversations");
    return normalizeConversation(data);
  },

  createConversation(): Conversation {
    // Returns a temp local object; will be replaced by real server conversation on first message
    return {
      id: `local-${Date.now()}`,
      title: "New chat",
      updatedAt: Date.now(),
      messages: [],
    };
  },

  async deleteConversation(id: string): Promise<void> {
    if (id.startsWith("local-")) return;
    await request("DELETE", `/chat/conversations/${id}`);
  },

  async renameConversation(id: string, title: string): Promise<void> {
    if (id.startsWith("local-")) return;
    await request("PATCH", `/chat/conversations/${id}`, { title });
  },

  async sendMessage(
    conversationId: string,
    content: string
  ): Promise<{ user: Message; ai: Message; conversation: Conversation }> {
    const isLocal = conversationId.startsWith("local-");
    const data = await request<any>("POST", "/chat/query", {
      conversationId: isLocal ? undefined : conversationId,
      content,
    });
    return {
      user: normalizeMessage(data.user),
      ai: normalizeMessage(data.ai),
      conversation: normalizeConversation(data.conversation),
    };
  },

  // ── Documents ────────────────────────────────────────────────────────────
  async listDocumentsAsync(): Promise<UploadedDoc[]> {
    const data = await request<any[]>("GET", "/documents");
    return data.map(normalizeDoc);
  },

  listDocuments(): UploadedDoc[] {
    return [];
  },

  async uploadDocument(
    file: File,
    onProgress?: (pct: number) => void
  ): Promise<UploadedDoc> {
    // Simulate early progress while waiting for the server
    onProgress?.(10);
    const formData = new FormData();
    formData.append("file", file);

    onProgress?.(30);

    const token = getToken();
    const res = await fetch(`${BASE_URL}/documents`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    onProgress?.(90);

    if (!res.ok) {
      let detail = `Upload failed (${res.status})`;
      try {
        const err = await res.json();
        detail = err.detail ?? detail;
      } catch { /* ignore */ }
      throw new Error(detail);
    }

    const data = await res.json();
    onProgress?.(100);
    return normalizeDoc(data);
  },

  async deleteDocument(id: string): Promise<void> {
    await request("DELETE", `/documents/${id}`);
  },

  // ── Report ───────────────────────────────────────────────────────────────
  async downloadChatReport(conversation: Conversation): Promise<void> {
    if (conversation.id.startsWith("local-") || conversation.messages.length === 0) {
      // Fallback: client-side markdown generation
      _downloadLocalReport(conversation);
      return;
    }
    const token = getToken();
    const res = await fetch(`${BASE_URL}/chat/report/${conversation.id}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("Failed to download report");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `intellecta-${conversation.title.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

function _downloadLocalReport(conversation: Conversation) {
  const lines: string[] = [
    `# Intellecta Chat Report`,
    `**Conversation:** ${conversation.title}`,
    `**Exported:** ${new Date().toLocaleString()}`,
    "",
  ];
  for (const m of conversation.messages) {
    lines.push(`## ${m.role === "user" ? "You" : "Intellecta"} — ${new Date(m.createdAt).toLocaleTimeString()}`);
    lines.push("");
    lines.push(m.content);
    if (m.sources?.length) {
      lines.push("");
      lines.push("**Sources:**");
      m.sources.forEach((s, i) => lines.push(`${i + 1}. ${s.documentName} (p. ${s.page}) — "${s.snippet}"`));
    }
    lines.push("");
  }
  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `intellecta-${conversation.title.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-${Date.now()}.md`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
