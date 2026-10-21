"use client";

import { ArrowLeft, Download } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, type Job, type Voice } from "../../lib/api";
import { isWorking } from "../../lib/job";
import { Alert } from "../ui/feedback";
import { ClientCard } from "./client-card";
import { EmailDialog } from "./email-dialog";

/* Steps 2-3: progress, per-client review, Word download. */
export function Run({ job, onJob, onBack, onReset }: { job: Job; onJob: (j: Job) => void; onBack: () => void; onReset: () => void }) {
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const [voice, setVoice] = useState<Voice | null>(null);

  useEffect(() => {
    api.voice().then(setVoice).catch(() => {});
  }, []);

  const working = isWorking(job);

  useEffect(() => {
    if (!working || job.status === "error") return;
    const t = setInterval(() => api.job(job.id).then(onJob).catch(() => {}), 1500);
    return () => clearInterval(t);
  }, [working, job.id, job.status, onJob]);

  const refresh = useCallback(() => api.job(job.id).then(onJob), [job.id, onJob]);

  async function download() {
    setSaving(true);
    setSaveError("");
    setSaved("");
    try {
      // Save any text edits first so the file contains exactly what is on screen.
      await Promise.all(Object.entries(edits).map(([name, body]) => api.patch(job.id, name, { body })));
      setEdits({});
      setSaved(await api.downloadDocx(job.id));
      await refresh();
    } catch (e) {
      setSaveError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (job.status === "error")
    return (
      <div className="max-w-2xl space-y-4">
        <Alert>Something went wrong: {job.error}</Alert>
        <button onClick={onReset} className="btn btn-outline">Back to setup</button>
      </div>
    );

  const done = job.clients.filter((c) => c.status === "ok" || c.status === "failed").length;
  const selected = job.clients.filter((c) => c.include && c.status === "ok").length;
  const ready = job.status === "ready" && !working;

  return (
    <div className="space-y-8 pb-24">
      <section className="card rise p-6" aria-live="polite">
        <div className="mb-3 flex items-baseline justify-between gap-4">
          <span className="font-semibold text-indigo">{job.message}</span>
          <span className="font-display text-sm font-semibold text-grey-600">{done}/{job.clients.length}</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-grey-100">
          <div
            className="h-full origin-left bg-brand transition-transform duration-[var(--dur-slow)] ease-[var(--ease-out)]"
            style={{ transform: `scaleX(${job.clients.length ? done / job.clients.length : 0})` }}
          />
        </div>
        {job.status === "signing_in" && (
          <p className="mt-3 text-brand-600">A Google sign-in window should open. Log in with the team account and press Allow.</p>
        )}
      </section>

      <div className="space-y-8">
        {job.clients.map((c, i) => (
          <ClientCard
            key={c.name}
            i={Math.min(i, 6)}
            job={job}
            c={c}
            text={edits[c.name] ?? c.body}
            onOpen={() => setOpen(c.name)}
            onInclude={(v) => api.patch(job.id, c.name, { include: v }).then(refresh)}
            onRetry={() => api.retry(job.id, c.name).then(refresh)}
          />
        ))}
      </div>

      {job.clients.map((c) =>
        c.name === open ? (
          <EmailDialog
            key={c.name}
            job={job}
            c={c}
            text={edits[c.name] ?? c.body}
            onText={(v) => setEdits((e) => ({ ...e, [c.name]: v }))}
            styles={voice?.styles ?? []}
            onRegenerate={async (prompt, styleId) => {
              await api.regenerate(job.id, c.name, prompt, styleId);
              setEdits((e) => {
                const rest = { ...e };
                delete rest[c.name];
                return rest;
              });
              await refresh();
            }}
            onClose={() => setOpen(null)}
          />
        ) : null,
      )}

      {saveError && <Alert>{saveError}</Alert>}
      {job.error && ready && <Alert>{job.error}</Alert>}
      {saved && <Alert tone="info">Downloaded {saved}. Open a client card to edit its email, then download again if anything needs changing.</Alert>}

      <div className="pointer-events-none fixed inset-x-0 bottom-6 z-[100] flex justify-center px-4">
        <div className="pointer-events-auto flex max-w-full items-center gap-x-5 gap-y-2 rounded-full border border-grey-200 bg-white/95 py-2.5 pl-2.5 pr-6 shadow-[var(--shadow-lg)] backdrop-blur">
          <button type="button" onClick={onBack} className="btn btn-outline">
            <ArrowLeft size={16} />
            Setup
          </button>
          <button type="button" disabled={!ready || saving || selected === 0} onClick={download} className="btn btn-primary">
            <Download size={18} />
            {saving ? "Preparing file" : "Download Word file"}
          </button>
          <span className="hidden text-sm text-grey-600 sm:inline">{selected} of {job.clients.length} included</span>
          <button type="button" onClick={onReset} className="btn-link whitespace-nowrap text-sm">Start over</button>
        </div>
      </div>
    </div>
  );
}
