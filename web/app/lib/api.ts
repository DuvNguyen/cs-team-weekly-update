export type PartTag = "template" | "gsc" | "notes" | "sheet" | "ai" | "trend" | "you";
export type PartCheck = {
  tags: PartTag[];
  numbers: { matched: string[]; unmatched: string[] };
  lines: { text: string; tag: "notes" | "flag" }[];
  flags: string[];
};
export type Part = {
  id: string;
  kind: "greeting" | "section" | "notes" | "trends" | "trend" | "signoff";
  title: string;
  text: string;
  status: "review" | "confirmed" | "deleted";
  edited: boolean;
  optional?: boolean;   // left out of the email unless confirmed
  check: PartCheck;
};

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
  trends_note: string;   // why there is no SEO trends / news part ('' when there is one)
  parts: Part[];
  parts_reviewed: number;
  parts_total: number;
  ready: boolean;
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
export type Source = "email" | "ai" | "you" | "none" | "";   // where a heading or note came from
export type Section = { id: string; title: string; instruction: string; enabled: boolean; title_source?: Source; instruction_source?: Source };
export type DraftSection = { id: string; title: string; title_source: Source; excerpt: string; found: boolean; start: number | null; end: number | null; note: string; note_source: Source };
export type StructureDraft = { email: string; sections: DraftSection[] };
export type Style = { id: string; name: string; persona: string; style: Rule[]; avoid: Rule[]; examples: Example[]; structure: Section[] };
export type Voice = { styles: Style[]; default_id: string };

export type ClientConfig = { name: string; property: string; category: string; contact?: string };   // contact = greeting name ("Ben" -> "Hi Ben,")

export type Config = {
  clients: ClientConfig[];
  seo_sheet_tab: string;
  demo: boolean;
  period: { start: string; end: string };
};

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export type AmSettings = { submitter: string; reviewer: string; dev_roster: string[]; seo_roster: string[] };
export type AmData = {
  submitter: string;
  reviewer: string;
  date_text: string;
  dev_pictures: string[];
  seo_pictures: string[];
  last_week: string[];
  this_week: string[];
  blockers: string[];
  answers: Record<string, string>;
};
export type AmItem = { key: string; label: string; text: string; answer: string | null; lists?: string[] };
export type AmTemplate = {
  title: string;
  sections: { heading: string; subsections: { heading: string | null; objective: string; items: AmItem[] }[] }[];
};
export type AmPicture = { section: "dev" | "seo"; person: string; name: string; url: string };
export type AmResult = { week_start: string; data: AmData; pictures: AmPicture[]; blank: string[]; warnings: string[]; idle: string[] };

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
  putClients: (rows: ClientConfig[]) => call<{ ok: boolean }>("/api/clients", send("PUT", rows)),
  setupStatus: () => call<{ client_secret: boolean }>("/api/setup-status"),
  settings: () => call<Settings>("/api/settings"),
  importClientSecret: (content: string) => call<{ ok: boolean }>("/api/settings/client-secret", send("PUT", { content })),
  importEnv: (content: string) => call<{ updated: string[] }>("/api/settings/env", send("PUT", { content })),
  voice: () => call<Voice>("/api/voice"),
  saveVoice: (v: Voice) => call<Voice>("/api/voice", send("PUT", v)),
  analyzeStructure: (email: string) => call<StructureDraft>("/api/voice/structure/analyze", send("POST", { email })),
  analyzeStyle: (email: string) => call<Style>("/api/voice/analyze", send("POST", { email })),
  resetVoice: () => call<Voice>("/api/voice/reset", send("POST")),
  period: () => call<{ end: string }>("/api/period"),
  tabs: () => call<{ tabs: string[] }>("/api/tabs"),
  startJob: (b: { tab: string; clients: string[]; start: string; end: string; style_id?: string }) =>
    call<Job>("/api/jobs", send("POST", b)),
  job: (id: string) => call<Job>(`/api/jobs/${id}`),
  patchPart: (id: string, name: string, partId: string, b: { title?: string; text?: string; status?: Part["status"] }) =>
    call<ClientRow>(`/api/jobs/${id}/clients/${encodeURIComponent(name)}/parts/${partId}`, send("PATCH", b)),
  movePart: (id: string, name: string, partId: string, direction: "up" | "down") =>
    call<ClientRow>(`/api/jobs/${id}/clients/${encodeURIComponent(name)}/parts/${partId}/move`, send("POST", { direction })),
  confirmAllParts: (id: string, name: string) =>
    call<{ client: ClientRow; confirmed: number; with_warnings: number }>(`/api/jobs/${id}/clients/${encodeURIComponent(name)}/parts/confirm-all`, send("POST")),
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
  amTemplate: () => call<AmTemplate>("/api/am-report/template"),
  amSettings: () => call<AmSettings>("/api/am-report/settings"),
  saveAmSettings: (v: AmSettings) => call<AmSettings>("/api/am-report/settings", send("PUT", v)),
  amGenerate: (week: string) => call<AmResult>("/api/am-report/generate", send("POST", { week })),
  amExport: async (week_start: string, data: AmData) => {
    const res = await fetch("/api/am-report/export", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ week_start, data }),
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        detail = (await res.json()).detail ?? detail;
      } catch {}
      throw new Error(detail);
    }
    const name = /filename\*?=(?:utf-8'')?"?([^";]+)"?/i.exec(res.headers.get("content-disposition") ?? "")?.[1];
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = name ? decodeURIComponent(name) : "Account Manager Report.docx";
    a.click();
    URL.revokeObjectURL(url);
  },
  chartUrl: (id: string, name: string) => `/api/jobs/${id}/chart/${encodeURIComponent(name)}`,
};
