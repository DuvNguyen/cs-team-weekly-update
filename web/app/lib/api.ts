export type Totals = { clicks: number; impressions: number; ctr: string; position: string };

export type ClientRow = {
  name: string;
  property: string;
  category: string;
  status: "pending" | "running" | "ok" | "failed";
  error: string;
  include: boolean;
  totals: Totals | null;
  prev_totals: Totals | null;
  body: string;
  has_chart: boolean;
  style_id: string;
  style_name: string;
};

export type Job = {
  id: string;
  status: "queued" | "signing_in" | "running" | "ready" | "publishing" | "done" | "error";
  message: string;
  tab: string;
  start: string;
  end: string;
  clients: ClientRow[];
  doc_url: string;
  error: string;
};

export type Rule = { id: string; text: string; enabled: boolean };
export type Example = { id: string; label: string; text: string; enabled: boolean };
export type Style = { id: string; name: string; persona: string; style: Rule[]; avoid: Rule[]; examples: Example[] };
export type Voice = { styles: Style[]; default_id: string };

export type Config = {
  clients: { name: string; property: string; category: string }[];
  seo_sheet_tab: string;
  demo: boolean;
  period: { start: string; end: string };
};

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export type Settings = { client_secret: boolean; gemini_key: string };

export type Me = { email: string; name: string; picture: string; demo: boolean };

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: init?.body ? { "content-type": "application/json" } : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

const send = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const api = {
  me: () => call<Me>("/api/auth/me"),
  logout: () => call<{ ok: boolean }>("/api/auth/logout", send("POST")),
  config: () => call<Config>("/api/config"),
  setupStatus: () => call<{ client_secret: boolean }>("/api/setup-status"),
  settings: () => call<Settings>("/api/settings"),
  importClientSecret: (content: string) => call<{ ok: boolean }>("/api/settings/client-secret", send("PUT", { content })),
  importEnv: (content: string) => call<{ updated: string[] }>("/api/settings/env", send("PUT", { content })),
  voice: () => call<Voice>("/api/voice"),
  saveVoice: (v: Voice) => call<Voice>("/api/voice", send("PUT", v)),
  analyzeStyle: (email: string) => call<Style>("/api/voice/analyze", send("POST", { email })),
  resetVoice: () => call<Voice>("/api/voice/reset", send("POST")),
  period: () => call<{ end: string }>("/api/period"),
  tabs: () => call<{ tabs: string[] }>("/api/tabs"),
  startJob: (b: { tab: string; clients: string[]; start: string; end: string; style_id?: string }) =>
    call<Job>("/api/jobs", send("POST", b)),
  job: (id: string) => call<Job>(`/api/jobs/${id}`),
  patch: (id: string, name: string, b: { body?: string; include?: boolean }) =>
    call<ClientRow>(`/api/jobs/${id}/clients/${encodeURIComponent(name)}`, send("PATCH", b)),
  retry: (id: string, name: string) =>
    call<ClientRow>(`/api/jobs/${id}/clients/${encodeURIComponent(name)}/retry`, send("POST")),
  regenerate: (id: string, name: string, prompt: string, style_id?: string) =>
    call<ClientRow>(`/api/jobs/${id}/clients/${encodeURIComponent(name)}/regenerate`, send("POST", { prompt, style_id })),
  publish: (id: string) => call<{ doc_url: string }>(`/api/jobs/${id}/publish`, send("POST")),
  downloadDocx: async (id: string) => {
    const res = await fetch(`/api/jobs/${id}/export`, { method: "POST" });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        detail = (await res.json()).detail ?? detail;
      } catch {}
      throw new Error(detail);
    }
    const name = /filename="([^"]+)"/.exec(res.headers.get("content-disposition") ?? "")?.[1] ?? "SEO-Report.docx";
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
    return name;
  },
  chartUrl: (id: string, name: string) => `/api/jobs/${id}/chart/${encodeURIComponent(name)}`,
};
