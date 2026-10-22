"use client";

import { ArrowDown, ArrowUp, Copy, Plus, RotateCcw, Save, Sparkles, Star, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Example, type Rule, type Section, type Style, type StructureDraft, type Voice } from "../../lib/api";
import { Card } from "../ui/card";
import { Checkbox } from "../ui/checkbox";
import { Alert, Skeleton } from "../ui/feedback";
import { SourceTag } from "../ui/source-tag";
import { StructureReview } from "./structure-review";

const uid = () => Math.random().toString(36).slice(2, 10);

/* A list of one-line rules: tick to switch off without deleting, edit in place, delete, add. */
function RuleList({ rules, onChange, placeholder }: { rules: Rule[]; onChange: (r: Rule[]) => void; placeholder: string }) {
  const [draft, setDraft] = useState("");
  const set = (id: string, patch: Partial<Rule>) => onChange(rules.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  const add = () => {
    if (!draft.trim()) return;
    onChange([...rules, { id: uid(), text: draft.trim(), enabled: true }]);
    setDraft("");
  };
  return (
    <div className="space-y-3">
      {rules.length === 0 && <p className="text-grey-600">No rules yet.</p>}
      <ul className="space-y-3">
        {rules.map((r) => (
          <li key={r.id} className={`flex items-start gap-3 transition-opacity duration-[var(--dur-fast)] ${r.enabled ? "" : "opacity-50"}`}>
            <span className="pt-2.5">
              <Checkbox checked={r.enabled} onChange={(v) => set(r.id, { enabled: v })}>
                <span className="sr-only">Use this rule</span>
              </Checkbox>
            </span>
            <textarea
              value={r.text}
              onChange={(e) => set(r.id, { text: e.target.value })}
              rows={2}
              aria-label="Rule text"
              className="field min-w-0 flex-1 resize-y leading-relaxed"
            />
            <button
              type="button"
              onClick={() => onChange(rules.filter((x) => x.id !== r.id))}
              aria-label="Delete rule"
              className="mt-1 grid size-10 shrink-0 place-items-center rounded-full text-grey-600 transition-colors duration-[var(--dur-fast)] hover:bg-danger-050 hover:text-danger"
            >
              <Trash2 size={18} />
            </button>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-3 pt-1">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder={placeholder}
          aria-label="New rule"
          className="field min-w-0 flex-1"
        />
        <button type="button" onClick={add} disabled={!draft.trim()} className="btn btn-outline">
          <Plus size={16} />
          Add
        </button>
      </div>
    </div>
  );
}

function ExampleList({ examples, onChange }: { examples: Example[]; onChange: (e: Example[]) => void }) {
  const set = (id: string, patch: Partial<Example>) => onChange(examples.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  return (
    <div className="space-y-5">
      {examples.length === 0 && <p className="text-grey-600">No examples. The model will write from the rules alone.</p>}
      {examples.map((e) => (
        <div key={e.id} className={`rounded-[var(--radius-md)] border border-grey-200 p-4 transition-opacity duration-[var(--dur-fast)] ${e.enabled ? "" : "opacity-50"}`}>
          <div className="mb-3 flex items-center gap-3">
            <Checkbox checked={e.enabled} onChange={(v) => set(e.id, { enabled: v })}>
              <span className="sr-only">Use this example</span>
            </Checkbox>
            <span className="text-sm font-semibold text-grey-600">Example of her writing</span>
            <input
              value={e.label}
              onChange={(ev) => set(e.id, { label: ev.target.value })}
              placeholder="when results are up"
              aria-label="When this example applies"
              className="field min-w-0 flex-1 !py-2"
            />
            <button
              type="button"
              onClick={() => onChange(examples.filter((x) => x.id !== e.id))}
              aria-label="Delete example"
              className="grid size-10 shrink-0 place-items-center rounded-full text-grey-600 transition-colors duration-[var(--dur-fast)] hover:bg-danger-050 hover:text-danger"
            >
              <Trash2 size={18} />
            </button>
          </div>
          <textarea
            value={e.text}
            onChange={(ev) => set(e.id, { text: ev.target.value })}
            rows={5}
            aria-label="Example text"
            className="field w-full resize-y leading-relaxed"
          />
        </div>
      ))}
      <button type="button" onClick={() => onChange([...examples, { id: uid(), label: "", text: "", enabled: true }])} className="btn btn-outline">
        <Plus size={16} />
        Add an example
      </button>
    </div>
  );
}

/* The email's sections in order: a heading (optional) and what goes under it. {period} / {next_period} in a heading become dates. */
function StructureEditor({ style, onChange }: { style: Section[]; onChange: (s: Section[]) => void }) {
  const [pasted, setPasted] = useState("");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [draft, setDraft] = useState<StructureDraft | null>(null);
  const set = (id: string, patch: Partial<Section>) => onChange(style.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  const move = (i: number, d: number) => {
    const next = [...style];
    [next[i], next[i + d]] = [next[i + d], next[i]];
    onChange(next);
  };
  async function fill() {
    setBusy(true);
    setErr("");
    try {
      setDraft(await api.analyzeStructure(pasted));
      setOpen(false);
      setPasted("");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (draft) {
    return (
      <StructureReview
        draft={draft}
        onSave={(sections) => {
          onChange(sections);
          setDraft(null);
        }}
        onCancel={() => setDraft(null)}
      />
    );
  }

  return (
    <div className="space-y-5">
      {style.length === 0 && <p className="text-grey-600">No sections. The email is one paragraph, followed by the SEO team&rsquo;s notes.</p>}
      <ul className="space-y-4">
        {style.map((r, i) => (
          <li key={r.id} className={`rounded-[var(--radius-md)] border border-grey-200 p-4 transition-opacity duration-[var(--dur-fast)] ${r.enabled ? "" : "opacity-50"}`}>
            <div className="mb-3 flex items-center gap-3">
              <Checkbox checked={r.enabled} onChange={(v) => set(r.id, { enabled: v })}>
                <span className="sr-only">Use this section</span>
              </Checkbox>
              <input
                value={r.title}
                onChange={(e) => set(r.id, { title: e.target.value, title_source: "you" })}
                placeholder="Heading (leave empty for plain paragraphs)"
                aria-label="Section heading"
                className="field min-w-0 flex-1 !py-2"
              />
              <button type="button" onClick={() => move(i, -1)} disabled={i === 0} aria-label="Move up" className="grid size-9 shrink-0 place-items-center rounded-full text-grey-600 hover:bg-grey-100 disabled:opacity-30">
                <ArrowUp size={16} />
              </button>
              <button type="button" onClick={() => move(i, 1)} disabled={i === style.length - 1} aria-label="Move down" className="grid size-9 shrink-0 place-items-center rounded-full text-grey-600 hover:bg-grey-100 disabled:opacity-30">
                <ArrowDown size={16} />
              </button>
              <button
                type="button"
                onClick={() => onChange(style.filter((x) => x.id !== r.id))}
                aria-label="Delete section"
                className="grid size-9 shrink-0 place-items-center rounded-full text-grey-600 transition-colors duration-[var(--dur-fast)] hover:bg-danger-050 hover:text-danger"
              >
                <Trash2 size={18} />
              </button>
            </div>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-grey-600">
              HEADING <SourceTag source={r.title_source} /> CONTENT <SourceTag source={r.instruction_source} />
            </div>
            <textarea
              value={r.instruction}
              onChange={(e) => set(r.id, { instruction: e.target.value, instruction_source: "you" })}
              rows={3}
              placeholder="What goes in this section, e.g. a bulleted list of the work done"
              aria-label="What goes in this section"
              className="field w-full resize-y leading-relaxed"
            />
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-3">
        <button type="button" onClick={() => onChange([...style, { id: uid(), title: "", instruction: "", enabled: true }])} className="btn btn-outline">
          <Plus size={16} />
          Add a section
        </button>
        <button type="button" onClick={() => setOpen(!open)} className="btn btn-outline">
          <Sparkles size={16} />
          Read sections from an email
        </button>
      </div>
      {open && (
        <div className="rounded-[var(--radius-md)] bg-grey-100 p-4">
          <label htmlFor="structure-email" className="label">Paste an email with the layout you want</label>
          <textarea
            id="structure-email"
            value={pasted}
            onChange={(e) => setPasted(e.target.value)}
            rows={8}
            placeholder="Paste a full email. Gemini proposes its sections, then you review each one before anything is replaced."
            className="field w-full resize-y leading-relaxed"
          />
          {err && <p className="mt-2 text-sm text-danger">{err}</p>}
          <div className="mt-3 flex gap-3">
            <button type="button" onClick={fill} disabled={!pasted.trim() || busy} className="btn btn-primary">
              <Sparkles size={16} />
              {busy ? "Reading the email" : "Read the email"}
            </button>
            <button type="button" onClick={() => setOpen(false)} className="btn-link">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

/* Several named writing styles. One is the default; a style is picked per report. */
export function VoiceManager() {
  const [saved, setSaved] = useState<Voice | null>(null);
  const [draft, setDraft] = useState<Voice | null>(null);
  const [sel, setSel] = useState("");
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [adding, setAdding] = useState(false);
  const [mode, setMode] = useState<"manual" | "email">("email");
  const [newName, setNewName] = useState("");
  const [pasted, setPasted] = useState("");
  const [drafting, setDrafting] = useState(false);

  useEffect(() => {
    api.voice().then((v) => {
      setSaved(v);
      setDraft(v);
      setSel(v.default_id);
    }).catch((e) => setError(e.message));
  }, []);

  if (!draft || !saved) return error ? <Alert>{error}</Alert> : <Skeleton className="h-96" />;

  const current = draft.styles.find((s) => s.id === sel) ?? draft.styles[0];
  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const update = (patch: Partial<Style>) => setDraft({ ...draft, styles: draft.styles.map((s) => (s.id === current.id ? { ...s, ...patch } : s)) });
  const addStyle = (s: Style) => {
    setDraft({ ...draft, styles: [...draft.styles, s] });
    setSel(s.id);
    setAdding(false);
    setNewName("");
    setPasted("");
  };

  async function run(fn: () => Promise<Voice>, message: string) {
    setBusy(true);
    setError("");
    setNote("");
    try {
      const v = await fn();
      setSaved(v);
      setDraft(v);
      setSel((id) => (v.styles.some((s) => s.id === id) ? id : v.default_id));
      setNote(message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      setConfirmReset(false);
    }
  }

  function createManual() {
    const base = draft!.styles.find((s) => s.id === draft!.default_id) ?? draft!.styles[0];
    addStyle({ id: uid(), name: newName.trim(), persona: base.persona, style: [], avoid: [], examples: [], structure: [] });
  }

  async function generate() {
    setDrafting(true);
    setError("");
    try {
      const s = await api.analyzeStyle(pasted);
      let name = newName.trim() || s.name;
      while (draft!.styles.some((x) => x.name.toLowerCase() === name.toLowerCase())) name += " 2";
      addStyle({ ...s, name });
      setNote("Drafted from your email. Read it, adjust anything, then press Save changes.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDrafting(false);
    }
  }

  function duplicate() {
    let name = `${current.name} copy`;
    while (draft!.styles.some((x) => x.name.toLowerCase() === name.toLowerCase())) name += " 2";
    const fresh = <T extends { id: string }>(rows: T[]) => rows.map((r) => ({ ...r, id: uid() }));
    addStyle({ ...current, id: uid(), name, style: fresh(current.style), avoid: fresh(current.avoid), examples: fresh(current.examples), structure: fresh(current.structure ?? []) });
  }

  function remove() {
    const styles = draft!.styles.filter((s) => s.id !== current.id);
    setDraft({ styles, default_id: draft!.default_id === current.id ? styles[0].id : draft!.default_id });
    setSel(styles[0].id);
  }

  const nameTaken = draft.styles.some((s) => s.name.toLowerCase() === newName.trim().toLowerCase());

  return (
    <div className="space-y-8 pb-24">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl">Writing styles</h2>
          <p className="mt-1 max-w-2xl text-grey-600">
            Each style tells Gemini how to write the client emails. Pick one when you set up a report, or switch it when you regenerate an email.
          </p>
        </div>
      </div>

      <div className="grid items-start gap-8 lg:grid-cols-12">
        <aside className="space-y-3 lg:col-span-3" aria-label="Styles">
          <ul className="space-y-2">
            {draft.styles.map((s) => {
              const on = s.id === current.id && !adding;
              return (
                <li key={s.id}>
                  <button
                    type="button"
                    aria-current={on ? "true" : undefined}
                    onClick={() => {
                      setSel(s.id);
                      setAdding(false);
                    }}
                    className={`flex w-full items-center justify-between gap-2 rounded-[var(--radius-sm)] border px-4 py-3 text-left transition-colors duration-[var(--dur-fast)] ${
                      on ? "border-brand bg-brand-050" : "border-grey-200 bg-white hover:border-grey-400"
                    }`}
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      {s.id === draft.default_id && <Star size={16} aria-hidden className="shrink-0 fill-sun text-sun" />}
                      <span className="min-w-0 truncate font-semibold text-indigo">{s.name}</span>
                    </span>
                    {s.id === draft.default_id && (
                      <span className="shrink-0 rounded-full bg-brand px-2.5 py-0.5 text-xs font-semibold text-white">
                        Default{draft.default_id !== saved.default_id ? " (unsaved)" : ""}
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
          <button type="button" onClick={() => setAdding(true)} className="btn btn-outline w-full">
            <Plus size={16} />
            Add style
          </button>
        </aside>

        <div className="space-y-8 lg:col-span-9">
          {adding ? (
            <Card title="Add a style" i={0}>
              <div className="mb-5 inline-flex gap-1 rounded-full bg-grey-100 p-1" role="tablist">
                {([["email", "From an email"], ["manual", "Write it myself"]] as const).map(([m, label]) => (
                  <button
                    key={m}
                    type="button"
                    role="tab"
                    aria-selected={mode === m}
                    onClick={() => setMode(m)}
                    className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors duration-[var(--dur-fast)] ${mode === m ? "bg-white text-indigo shadow-[var(--shadow-xs)]" : "text-grey-600 hover:text-indigo"}`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <label htmlFor="new-name" className="label">Name {mode === "email" && <span className="font-normal text-grey-600">(optional, Gemini suggests one)</span>}</label>
              <input id="new-name" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g. Casual, Formal, Monthly recap" className="field mb-5" />

              {mode === "email" ? (
                <>
                  <label htmlFor="pasted" className="label">Paste an email whose style you like</label>
                  <textarea
                    id="pasted"
                    value={pasted}
                    onChange={(e) => setPasted(e.target.value)}
                    rows={9}
                    placeholder="Paste a full email. Gemini describes how it is written and drafts the rules for you to review."
                    className="field w-full resize-y leading-relaxed"
                  />
                  <p className="mt-2 text-sm text-grey-600">Nothing is saved until you review the result and press Save changes. The email is also kept as an example for the style.</p>
                  <div className="mt-5 flex gap-3">
                    <button type="button" onClick={generate} disabled={!pasted.trim() || drafting || (!!newName.trim() && nameTaken)} className="btn btn-primary">
                      <Sparkles size={16} />
                      {drafting ? "Reading the email" : "Generate style"}
                    </button>
                    <button type="button" onClick={() => setAdding(false)} className="btn-link">Cancel</button>
                  </div>
                </>
              ) : (
                <div className="flex gap-3">
                  <button type="button" onClick={createManual} disabled={!newName.trim() || nameTaken} className="btn btn-primary">
                    <Plus size={16} />
                    Create style
                  </button>
                  <button type="button" onClick={() => setAdding(false)} className="btn-link">Cancel</button>
                </div>
              )}
              {!!newName.trim() && nameTaken && <p className="mt-3 text-sm text-danger">A style with that name already exists.</p>}
            </Card>
          ) : (
            <>
              <Card
                title="Style"
                i={0}
                aside={
                  <div className="flex flex-wrap items-center gap-2">
                    {current.id === draft.default_id ? (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-brand px-3 py-1 text-xs font-semibold text-white">
                        <Star size={12} aria-hidden className="fill-sun text-sun" />
                        Default style
                      </span>
                    ) : (
                      <button type="button" onClick={() => setDraft({ ...draft, default_id: current.id })} className="btn-link inline-flex items-center gap-1.5 text-sm">
                        <Star size={14} />
                        Make default
                      </button>
                    )}
                    <button type="button" onClick={duplicate} className="btn-link inline-flex items-center gap-1.5 text-sm">
                      <Copy size={14} />
                      Duplicate
                    </button>
                    <button
                      type="button"
                      onClick={remove}
                      disabled={draft.styles.length < 2}
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-danger hover:underline disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                }
              >
                <label htmlFor="style-name" className="label">Name</label>
                <input id="style-name" value={current.name} onChange={(e) => update({ name: e.target.value })} className="field mb-5" />
                <label htmlFor="persona" className="label">Opening line (who is writing)</label>
                <textarea id="persona" value={current.persona} onChange={(e) => update({ persona: e.target.value })} rows={2} className="field w-full resize-y leading-relaxed" />
              </Card>

              <Card title="Email structure" i={1} aside={<span className="text-sm text-grey-600">The sections the email is built from</span>}>
                <StructureEditor key={current.id} style={current.structure ?? []} onChange={(structure) => update({ structure })} />
              </Card>

              <Card title="Style rules" i={2} aside={<span className="text-sm text-grey-600">Things the writer should do</span>}>
                <RuleList key={current.id} rules={current.style} onChange={(style) => update({ style })} placeholder="e.g. Keep it under 120 words" />
              </Card>

              <Card title="Avoid" i={3} aside={<span className="text-sm text-grey-600">Things the writer must not do</span>}>
                <RuleList key={current.id} rules={current.avoid} onChange={(avoid) => update({ avoid })} placeholder="e.g. Exclamation marks" />
              </Card>

              <Card title="Examples" i={4} aside={<span className="text-sm text-grey-600">Real emails the model copies the tone from</span>}>
                <ExampleList examples={current.examples} onChange={(examples) => update({ examples })} />
              </Card>
            </>
          )}
        </div>
      </div>

      {error && <Alert>{error}</Alert>}
      {note && <Alert tone="info">{note}</Alert>}

      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-grey-200 pt-6">
        <span className="text-sm text-grey-600">{dirty ? "You have unsaved changes." : "All changes saved."}</span>
        <div className="flex flex-wrap items-center gap-3">
          {confirmReset ? (
            <>
              <span className="text-sm text-grey-600">Delete all styles and restore the original?</span>
              <button type="button" disabled={busy} onClick={() => run(api.resetVoice, "Restored the original style.")} className="btn btn-outline">Yes, reset</button>
              <button type="button" onClick={() => setConfirmReset(false)} className="btn-link text-sm">Cancel</button>
            </>
          ) : (
            <button type="button" disabled={busy} onClick={() => setConfirmReset(true)} className="btn-link inline-flex items-center gap-1.5 text-sm">
              <RotateCcw size={14} />
              Reset to default
            </button>
          )}
          <button type="button" disabled={!dirty || busy} onClick={() => run(() => api.saveVoice(draft), "Saved. New emails can use these styles.")} className="btn btn-primary">
            <Save size={16} />
            {busy ? "Saving" : "Save changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
