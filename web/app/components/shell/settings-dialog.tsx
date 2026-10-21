"use client";

import { Check, KeyRound, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, type Settings } from "../../lib/api";
import { Alert } from "../ui/feedback";

/* Import the Google client secret and the .env values from inside the app. Works before sign-in too. */
export function SettingsDialog({ open, onClose, onChanged }: { open: boolean; onClose: () => void; onChanged: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [notice, setNotice] = useState<{ tone: "error" | "info"; text: string } | null>(null);
  const [key, setKey] = useState("");

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      d.showModal();
      setNotice(null);
      api.settings().then(setSettings).catch(() => api.setupStatus().then((s) => setSettings({ ...s, gemini_key: "" })).catch(() => {}));
    }
    if (!open && d.open) d.close();
  }, [open]);

  async function run(job: () => Promise<string>) {
    try {
      setNotice({ tone: "info", text: await job() });
      setSettings(await api.settings().catch(() => api.setupStatus().then((s) => ({ ...s, gemini_key: "" }))));
      onChanged();
    } catch (e) {
      setNotice({ tone: "error", text: e instanceof Error ? e.message : "Something went wrong." });
    }
  }

  const importFile = (kind: "secret" | "env") => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    run(async () => {
      const text = await file.text();
      if (kind === "secret") {
        await api.importClientSecret(text);
        return "Google client secret imported.";
      }
      const { updated } = await api.importEnv(text);
      return `Imported ${updated.join(", ")}.`;
    });
  };

  return (
    <dialog ref={ref} onClose={onClose} onClick={(e) => e.target === ref.current && onClose()} className="m-auto w-[min(32rem,calc(100vw-2rem))] rounded-[var(--radius-lg)] p-0 backdrop:bg-navy/60">
      <div className="space-y-6 p-8">
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-2xl">Settings</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-full p-1.5 text-grey-600 hover:bg-grey-100">
            <X size={18} />
          </button>
        </div>

        {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}

        <section className="space-y-2">
          <h3 className="flex items-center gap-2 text-base font-semibold">
            Google client secret {settings?.client_secret && <Check size={16} className="text-brand" aria-label="Imported" />}
          </h3>
          <p className="text-sm text-grey-600">The <code>client_secret.json</code> file from your admin. Needed to sign in with Google.</p>
          <label className="btn btn-secondary cursor-pointer">
            <KeyRound size={16} />
            {settings?.client_secret ? "Replace file…" : "Choose file…"}
            <input type="file" accept=".json,application/json" className="sr-only" onChange={importFile("secret")} />
          </label>
        </section>

        <section className="space-y-2">
          <h3 className="flex items-center gap-2 text-base font-semibold">
            Gemini API key {settings?.gemini_key && <span className="text-sm font-normal text-grey-600">{settings.gemini_key}</span>}
          </h3>
          <p className="text-sm text-grey-600">Import the <code>.env</code> file, or paste the key.</p>
          <div className="flex flex-wrap items-center gap-3">
            <label className="btn btn-secondary cursor-pointer">
              Import .env…
              <input type="file" className="sr-only" onChange={importFile("env")} />
            </label>
            <form
              className="flex min-w-0 flex-1 gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                const k = key.trim();
                if (k) run(async () => (await api.importEnv(`GEMINI_API_KEY=${k}`), setKey(""), "Gemini key saved."));
              }}
            >
              <input type="password" value={key} onChange={(e) => setKey(e.target.value)} placeholder="Paste key" autoComplete="off" className="min-w-0 flex-1 rounded-[var(--radius-md)] border border-grey-200 px-3 py-2 text-sm" />
              <button type="submit" disabled={!key.trim()} className="btn btn-primary !text-white">Save</button>
            </form>
          </div>
        </section>
      </div>
    </dialog>
  );
}
