"use client";

import { Sparkles, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, type ClientRow, type Job, type Style } from "../../lib/api";
import { Combobox } from "../ui/combobox";
import { Alert } from "../ui/feedback";
import { EmailParts } from "./email-parts";
import { Stats } from "./stats";

/* Full editor for one client's email: edit by hand, or rewrite with a prompt. */
export function EmailDialog(props: {
  job: Job;
  c: ClientRow;
  onChanged: () => Promise<unknown>;
  styles: Style[];
  onRegenerate: (prompt: string, styleId: string) => Promise<void>;
  onClose: () => void;
}) {
  const { job, c, onChanged, styles, onRegenerate, onClose } = props;
  const ref = useRef<HTMLDialogElement>(null);
  const [prompt, setPrompt] = useState("");
  const [styleId, setStyleId] = useState(c.style_id);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
  }, []);

  async function rewrite() {
    setBusy(true);
    setError("");
    try {
      await onRegenerate(prompt, styleId);
      setPrompt("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === ref.current) ref.current?.close();
      }}
      className="m-auto w-[min(72rem,calc(100vw-2rem))] max-w-none overflow-hidden rounded-[var(--radius-lg)] bg-white p-0 shadow-[var(--shadow-lg)] backdrop:bg-[rgba(6,21,40,0.55)]"
    >
      <div className="flex max-h-[calc(100dvh-2rem)] flex-col">
        <header className="flex items-start justify-between gap-4 border-b border-grey-200 px-8 py-5">
          <div>
            <h2 className="text-2xl">{c.name}</h2>
            <p className="text-sm text-grey-600">Email to the client &middot; {job.start} to {job.end}</p>
          </div>
          <button type="button" onClick={() => ref.current?.close()} aria-label="Close" className="grid size-10 place-items-center rounded-full text-grey-600 hover:bg-grey-100">
            <X size={20} />
          </button>
        </header>

        <div className="grid gap-8 overflow-y-auto px-8 py-6 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`${api.chartUrl(job.id, c.name)}?t=${c.totals?.clicks}-${c.totals?.impressions}`}
              alt={`Clicks and impressions for ${c.name}`}
              className="w-full rounded-[var(--radius-md)] border border-grey-200"
            />
            {c.totals && c.prev_totals && <Stats now={c.totals} prev={c.prev_totals} />}
          </div>

          <div className="flex flex-col lg:col-span-7">
            <EmailParts job={job} c={c} onChanged={onChanged} />

            {styles.length > 1 && (
              <div className="mt-5">
                <Combobox
                  label="Writing style"
                  value={styleId}
                  onChange={setStyleId}
                  options={styles.map((x) => ({ value: x.id, label: x.name }))}
                />
              </div>
            )}

            <label htmlFor="email-prompt" className="label mt-5">Rewrite with a prompt</label>
            <div className="flex flex-wrap gap-3">
              <input
                id="email-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !busy) rewrite();
                }}
                placeholder="e.g. shorter, more upbeat, mention the new landing page"
                className="field min-w-0 flex-1"
              />
              <button type="button" onClick={rewrite} disabled={busy} className="btn btn-outline">
                <Sparkles size={16} />
                {busy ? "Rewriting" : prompt.trim() ? "Regenerate with prompt" : "Regenerate"}
              </button>
            </div>
            <p className="mt-2 text-sm text-grey-600">Regenerating replaces all the parts above with a fresh email. Your edits and confirmations are lost.</p>
            {error && <div className="mt-3"><Alert>{error}</Alert></div>}
          </div>
        </div>

        <footer className="flex justify-end border-t border-grey-200 px-8 py-4">
          <button type="button" onClick={() => ref.current?.close()} className="btn btn-primary">Done</button>
        </footer>
      </div>
    </dialog>
  );
}
