"use client";

import { Check, Pencil, Save, Trash2, Undo2 } from "lucide-react";
import { useState } from "react";
import { api, type ClientRow, type Job, type Part } from "../../lib/api";
import { Alert, Badge } from "../ui/feedback";
import { PartTag } from "../ui/part-tag";

/* One part of the email: heading, content, where it came from, and Confirm / Edit / Delete. */
function PartCard({ part, busy, onPatch }: { part: Part; busy: boolean; onPatch: (b: { title?: string; text?: string; status?: Part["status"] }) => Promise<void> }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(part.title);
  const [text, setText] = useState(part.text);
  const { check } = part;
  const flagged = check.flags.length > 0;
  const deleted = part.status === "deleted";
  const confirmed = part.status === "confirmed";
  const lineTags = new Map(check.lines.map((l) => [l.text.trim(), l.tag]));
  const label = part.title || { greeting: "Greeting", signoff: "Sign-off", section: "Paragraph", notes: "SEO team notes", trend: "Industry trend" }[part.kind];

  async function save() {
    await onPatch({ title, text });
    setEditing(false);
  }

  return (
    <li
      className={`rounded-[var(--radius-md)] border-l-4 bg-white p-4 shadow-[var(--shadow-xs)] ${deleted ? "opacity-60" : ""}`}
      style={{ borderLeftColor: confirmed ? "#22c55e" : flagged ? "#d64545" : "#3165f5" }}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <strong className={deleted ? "line-through" : "text-indigo"}>{label}</strong>
        {confirmed ? <Badge tone="green">Confirmed</Badge> : deleted ? <Badge>Deleted</Badge> : <Badge tone={flagged ? "danger" : "blue"}>{flagged ? "Check this" : "Needs review"}</Badge>}
      </div>

      {deleted ? (
        <button type="button" disabled={busy} onClick={() => onPatch({ status: "review" })} className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-brand">
          <Undo2 size={14} /> Undo
        </button>
      ) : (
        <div className="mt-2 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            {check.tags.map((t) => (
              <PartTag key={t} tag={t} />
            ))}
            {check.numbers.matched.length > 0 && <span className="text-xs text-grey-600">{check.numbers.matched.length} number{check.numbers.matched.length === 1 ? "" : "s"} match Search Console</span>}
          </div>

          {editing ? (
            <div className="space-y-2">
              {(part.kind === "section" || part.kind === "notes" || part.kind === "trend") && (
                <input className="field !py-1.5" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Heading (empty for plain paragraphs)" aria-label="Heading" />
              )}
              <textarea className="field min-h-32 max-h-[60vh] [field-sizing:content]" value={text} onChange={(e) => setText(e.target.value)} aria-label={`${label} text`} />
            </div>
          ) : (
            <div className="space-y-1 whitespace-pre-wrap leading-relaxed">
              {part.title && <p className="text-sm text-grey-600">Heading: {part.title}</p>}
              {part.text.split("\n").map((line, i) => {
                const tag = lineTags.get(line.trim());
                return (
                  <p key={i} className={tag === "flag" ? "rounded bg-danger-050 px-1" : ""}>
                    {line || " "}
                    {tag === "notes" && <span className="ml-2 align-middle"><Badge tone="green">SEO team notes</Badge></span>}
                    {tag === "flag" && <span className="ml-2 align-middle"><Badge tone="danger">Not in the sources</Badge></span>}
                  </p>
                );
              })}
            </div>
          )}

          {flagged && (
            <Alert>
              {check.flags[0]}
              {check.flags.length > 1 ? ` (and ${check.flags.length - 1} more)` : ""} Edit it so it matches the sources, or delete it.
            </Alert>
          )}

          <div className="flex flex-wrap gap-2">
            {editing ? (
              <>
                <button type="button" disabled={busy} onClick={save} className="btn btn-primary !px-3 !py-1 text-sm !text-white">
                  <Save size={14} /> Save changes
                </button>
                <button type="button" onClick={() => (setEditing(false), setTitle(part.title), setText(part.text))} className="btn btn-outline !px-3 !py-1 text-sm">Cancel</button>
              </>
            ) : (
              <>
                {!confirmed && (
                  <button
                    type="button"
                    disabled={busy || (flagged && !part.edited)}
                    title={flagged && !part.edited ? "Edit this part first, or delete it" : ""}
                    onClick={() => onPatch({ status: "confirmed" })}
                    className="btn btn-primary !px-3 !py-1 text-sm !text-white"
                  >
                    <Check size={14} /> Confirm
                  </button>
                )}
                <button type="button" onClick={() => (setTitle(part.title), setText(part.text), setEditing(true))} className="btn btn-outline !px-3 !py-1 text-sm">
                  <Pencil size={14} /> Edit
                </button>
                <button type="button" disabled={busy} onClick={() => onPatch({ status: "deleted" })} className="btn btn-outline !px-3 !py-1 text-sm !text-danger">
                  <Trash2 size={14} /> Delete
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </li>
  );
}

/* A client's email, part by part. Every change is saved at once; the email text is rebuilt from the parts. */
export function EmailParts({ job, c, onChanged }: { job: Job; c: ClientRow; onChanged: () => Promise<unknown> }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function patch(part: Part, b: { title?: string; text?: string; status?: Part["status"] }) {
    setBusy(true);
    setError("");
    try {
      await api.patchPart(job.id, c.name, part.id, b);
      await onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="label !mb-0">Email to the client, part by part</span>
        <span className="text-sm text-grey-600">{c.parts_reviewed} of {c.parts_total} parts reviewed</span>
      </div>
      <p className="text-sm text-grey-600">Read each part. <strong>Confirm</strong> what is right, <strong>Edit</strong> what isn&rsquo;t, <strong>Delete</strong> what you don&rsquo;t want. The tags show where each part comes from.</p>
      {error && <Alert>{error}</Alert>}
      <ol className="space-y-3">
        {c.parts.map((p) => (
          <PartCard key={`${p.id}-${p.text.length}-${p.status}`} part={p} busy={busy} onPatch={(b) => patch(p, b)} />
        ))}
      </ol>
    </div>
  );
}
