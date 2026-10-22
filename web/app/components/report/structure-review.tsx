"use client";

import { Check, Pencil, Trash2, Undo2 } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import type { DraftSection, Section, Source, StructureDraft } from "../../lib/api";
import { Badge } from "../ui/feedback";
import { SourceTag } from "../ui/source-tag";

type Status = "review" | "confirmed" | "deleted";
type Item = DraftSection & { status: Status; editing: boolean; titleSource: Source; noteSource: Source };

const COLORS = ["#e7f8ee", "#dde7fe", "#fff1d6", "#fde2e2", "#efe4fb", "#dcf3f7", "#f3ecd4", "#e4e8ee"];

/* Review a pasted email's sections: the email on the left with each section marked, one card per section on the right.
   Headings and notes are tagged with where they came from; nothing is saved until every section is confirmed or deleted. */
export function StructureReview({ draft, onSave, onCancel }: { draft: StructureDraft; onSave: (s: Section[]) => void; onCancel: () => void }) {
  const [items, setItems] = useState<Item[]>(() =>
    draft.sections.map((s) => ({ ...s, status: "review", editing: false, titleSource: s.title_source, noteSource: s.note_source })),
  );
  const [active, setActive] = useState<string | null>(null);
  const marks = useRef<Record<string, HTMLElement | null>>({});
  const patch = (id: string, p: Partial<Item>) => setItems((all) => all.map((x) => (x.id === id ? { ...x, ...p } : x)));

  // The email cut into plain and marked pieces. Sections that overlap an earlier one are not marked twice.
  const pieces = useMemo(() => {
    const found = items.map((x, i) => ({ x, i })).filter(({ x }) => x.found && x.start !== null && x.end !== null).sort((a, b) => a.x.start! - b.x.start!);
    const out: { text: string; id?: string; color?: string }[] = [];
    let at = 0;
    for (const { x, i } of found) {
      if (x.start! < at) continue;
      if (x.start! > at) out.push({ text: draft.email.slice(at, x.start!) });
      out.push({ text: draft.email.slice(x.start!, x.end!), id: x.id, color: COLORS[i % COLORS.length] });
      at = x.end!;
    }
    if (at < draft.email.length) out.push({ text: draft.email.slice(at) });
    return out;
  }, [items, draft.email]);

  const reviewed = items.filter((x) => x.status !== "review").length;
  const confirmed = items.filter((x) => x.status === "confirmed");
  const ready = reviewed === items.length && confirmed.length > 0;
  const focus = (id: string) => {
    setActive(id);
    marks.current[id]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-grey-600">
        Check each section against the email. <strong>Confirm</strong> what is right, <strong>Edit</strong> what isn&rsquo;t, <strong>Delete</strong> what you don&rsquo;t want. Nothing is saved until every section is reviewed.
      </p>
      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <div className="max-h-[32rem] overflow-y-auto whitespace-pre-wrap rounded-[var(--radius-md)] bg-white p-4 text-sm leading-relaxed">
          <p className="label !mb-2">The email you pasted</p>
          {pieces.map((p, i) =>
            p.id ? (
              <mark
                key={i}
                ref={(el) => {
                  marks.current[p.id!] = el;
                }}
                onClick={() => focus(p.id!)}
                style={{ backgroundColor: p.color }}
                className={`cursor-pointer rounded px-0.5 text-ink ${active === p.id ? "outline outline-2 outline-brand" : ""}`}
              >
                {p.text}
              </mark>
            ) : (
              <span key={i}>{p.text}</span>
            ),
          )}
        </div>

        <ol className="space-y-3">
          {items.map((x, i) => {
            const deleted = x.status === "deleted";
            return (
              <li
                key={x.id}
                onClick={() => focus(x.id)}
                className={`rounded-[var(--radius-md)] border-l-4 bg-white p-3 ${active === x.id ? "shadow-md" : ""} ${deleted ? "opacity-60" : ""}`}
                style={{ borderLeftColor: x.status === "confirmed" ? "#22c55e" : x.found ? COLORS[i % COLORS.length] : "#d64545" }}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <strong className={deleted ? "line-through" : ""}>{i + 1}. {x.title || "(no heading)"}</strong>
                  {x.status === "confirmed" ? <Badge tone="sky">Confirmed</Badge> : deleted ? null : !x.found ? <Badge tone="danger">Not found in the email</Badge> : <Badge tone="blue">Needs review</Badge>}
                </div>

                {deleted ? (
                  <button type="button" onClick={() => patch(x.id, { status: "review" })} className="mt-1 inline-flex items-center gap-1 text-sm font-semibold text-brand">
                    <Undo2 size={14} /> Undo
                  </button>
                ) : (
                  <div className="mt-2 space-y-2">
                    <div>
                      <div className="mb-1 flex items-center gap-2 text-xs text-grey-600">HEADING <SourceTag source={x.titleSource} /></div>
                      {x.editing ? (
                        <input className="field !py-1.5 text-sm" value={x.title} onChange={(e) => patch(x.id, { title: e.target.value, titleSource: "you" })} placeholder="Heading (empty for plain paragraphs)" aria-label="Heading" />
                      ) : (
                        <p className="text-sm">{x.title || <span className="text-grey-600">None</span>}</p>
                      )}
                    </div>
                    <div>
                      <div className="mb-1 flex items-center gap-2 text-xs text-grey-600">WHAT THIS SECTION IS <SourceTag source={x.noteSource} /></div>
                      {x.editing ? (
                        <textarea className="field min-h-20 text-sm" value={x.note} onChange={(e) => patch(x.id, { note: e.target.value, noteSource: "you" })} aria-label="What this section is" />
                      ) : (
                        <p className="text-sm">{x.note || <span className="text-grey-600">Empty</span>}</p>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {x.status !== "confirmed" && (
                        <button type="button" disabled={!x.found} title={x.found ? "" : "This text is not in the email, so it can't be confirmed"} onClick={() => patch(x.id, { status: "confirmed", editing: false })} className="btn btn-primary !px-3 !py-1 text-sm !text-white">
                          <Check size={14} /> Confirm
                        </button>
                      )}
                      <button type="button" onClick={() => patch(x.id, { editing: !x.editing, status: x.status === "confirmed" ? "review" : x.status })} className="btn btn-outline !px-3 !py-1 text-sm">
                        <Pencil size={14} /> {x.editing ? "Done" : "Edit"}
                      </button>
                      <button type="button" onClick={() => patch(x.id, { status: "deleted", editing: false })} className="btn btn-outline !px-3 !py-1 text-sm !text-danger">
                        <Trash2 size={14} /> Delete
                      </button>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-sm text-grey-600">{reviewed} of {items.length} reviewed</span>
        <div className="flex items-center gap-3">
          <button type="button" onClick={onCancel} className="btn-link">Cancel</button>
          <button
            type="button"
            disabled={!ready}
            onClick={() => onSave(confirmed.map((x) => ({ id: x.id, title: x.title, instruction: x.note, enabled: true, title_source: x.titleSource, instruction_source: x.noteSource })))}
            className="btn btn-primary !text-white"
          >
            Save structure
          </button>
        </div>
      </div>
    </div>
  );
}
