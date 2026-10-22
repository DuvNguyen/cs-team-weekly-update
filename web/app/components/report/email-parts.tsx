"use client";

import { ArrowDown, ArrowUp, Check, CheckCheck, Pencil, Save, Trash2, Undo2 } from "lucide-react";
import { useState } from "react";
import { api, type ClientRow, type Job, type Part } from "../../lib/api";
import { Alert, Badge } from "../ui/feedback";
import { PartTag } from "../ui/part-tag";

/* One part of the email: heading, content, where it came from, and Confirm / Edit / Delete. */
function PartCard({ part, busy, onPatch, onMove }: { part: Part; busy: boolean; onPatch: (b: { title?: string; text?: string; status?: Part["status"] }) => Promise<void>; onMove?: { up: (() => void) | null; down: (() => void) | null } }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(part.title);
  const [text, setText] = useState(part.text);
  const { check } = part;
  const flagged = check.flags.length > 0;
  const deleted = part.status === "deleted";
  const confirmed = part.status === "confirmed";
  const lineTags = new Map(check.lines.map((l) => [l.text.trim(), l.tag]));
  const label = part.title || { greeting: "Greeting", signoff: "Sign-off", section: "Paragraph", notes: "SEO team notes", trends: "SEO trends / news", trend: "Industry trend" }[part.kind];

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
        <div className="flex items-center gap-1.5">
          {onMove && (
            <span className="mr-1 inline-flex items-center gap-0.5">
              <button type="button" onClick={onMove.up ?? undefined} disabled={busy || !onMove.up} aria-label={`Move ${label} up`} title="Move up" className="grid size-7 place-items-center rounded-full text-grey-600 transition-colors duration-[var(--dur-fast)] hover:bg-grey-100 hover:text-ink disabled:opacity-30 disabled:hover:bg-transparent">
                <ArrowUp size={15} />
              </button>
              <button type="button" onClick={onMove.down ?? undefined} disabled={busy || !onMove.down} aria-label={`Move ${label} down`} title="Move down" className="grid size-7 place-items-center rounded-full text-grey-600 transition-colors duration-[var(--dur-fast)] hover:bg-grey-100 hover:text-ink disabled:opacity-30 disabled:hover:bg-transparent">
                <ArrowDown size={15} />
              </button>
            </span>
          )}
          {confirmed ? <Badge tone="green">Confirmed</Badge> : deleted ? <Badge>Deleted</Badge> : part.optional ? <Badge>Not in the email</Badge> : <Badge tone={flagged ? "danger" : "blue"}>{flagged ? "Check this" : "Needs review"}</Badge>}
        </div>
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

          {part.optional && !confirmed && <p className="text-sm text-grey-600">Optional: this stays out of the email and the document unless you confirm it.</p>}

          {editing ? (
            <div className="space-y-2">
              {(part.kind === "section" || part.kind === "notes" || part.kind === "trends" || part.kind === "trend") && (
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
  const [note, setNote] = useState("");
  // Parts "Confirm all" can confirm: still in review, and nothing flagged (or already edited by the person).
  const confirmable = c.parts.filter((p) => p.status === "review" && (p.check.flags.length === 0 || p.edited)).length;

  async function confirmAll() {
    setBusy(true);
    setError("");
    setNote("");
    try {
      const r = await api.confirmAllParts(job.id, c.name);
      await onChanged();
      if (r.needs_checking > 0) setNote(`Confirmed ${r.confirmed} part${r.confirmed === 1 ? "" : "s"}. ${r.needs_checking} still need${r.needs_checking === 1 ? "s" : ""} checking: edit ${r.needs_checking === 1 ? "it" : "them"} so it matches the sources, or delete ${r.needs_checking === 1 ? "it" : "them"}.`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function move(part: Part, direction: "up" | "down") {
    setBusy(true);
    setError("");
    try {
      await api.movePart(job.id, c.name, part.id, direction);
      await onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

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
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm text-grey-600">{c.parts_reviewed} of {c.parts_total} parts reviewed</span>
          <button
            type="button"
            onClick={confirmAll}
            disabled={busy || confirmable === 0}
            title="Confirms every part that has nothing flagged. Flagged parts stay for you to edit or delete."
            className="btn btn-primary !px-3 !py-1 text-sm !text-white"
          >
            <CheckCheck size={14} /> {confirmable > 0 ? `Confirm all (${confirmable})` : "Confirm all"}
          </button>
        </div>
      </div>
      <p className="text-sm text-grey-600">Read each part. <strong>Confirm</strong> what is right, <strong>Edit</strong> what isn&rsquo;t, <strong>Delete</strong> what you don&rsquo;t want. The tags show where each part comes from.</p>
      {error && <Alert>{error}</Alert>}
      {note && <Alert tone="info">{note}</Alert>}
      {c.trends_note && <Alert tone="info">{c.trends_note}</Alert>}
      <ol className="space-y-3">
        {c.parts.map((p, i) => {
          // The greeting stays first and the sign-off last; everything between can move.
          const fixed = p.kind === "greeting" || p.kind === "signoff";
          const onMove = fixed ? undefined : {
            up: c.parts[i - 1]?.kind === "greeting" ? null : () => move(p, "up"),
            down: c.parts[i + 1]?.kind === "signoff" ? null : () => move(p, "down"),
          };
          return <PartCard key={`${p.id}-${p.text.length}-${p.status}`} part={p} busy={busy} onPatch={(b) => patch(p, b)} onMove={onMove} />;
        })}
      </ol>
    </div>
  );
}
