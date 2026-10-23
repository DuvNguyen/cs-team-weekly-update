"use client";

import { Save } from "lucide-react";
import { useState } from "react";
import { api, type ClientConfig } from "../../lib/api";
import { Alert } from "../ui/feedback";
import { Card } from "../ui/card";
import { TagInput, joinTags, splitTags } from "../ui/tag-input";
import { useApp } from "../shell/app-shell";

const greeting = (c: ClientConfig) => `Hi ${c.contact?.trim() || `${c.name} team`},`;

/* Each client's details. "Greeting name" is what the email says: Ben makes it "Hi Ben,". */
export function ClientsEditor() {
  const { config, refreshConfig } = useApp();
  const [rows, setRows] = useState<ClientConfig[]>(() => config.clients.map((c) => ({ ...c })));
  const [saved, setSaved] = useState(config.clients);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const known = [...new Set(rows.flatMap((r) => splitTags(r.category)))].sort((a, b) => a.localeCompare(b));   // every tag already in use, offered as suggestions
  const dirty = JSON.stringify(rows) !== JSON.stringify(saved);

  const set = (i: number, patch: Partial<ClientConfig>) => (setDone(false), setRows((all) => all.map((r, n) => (n === i ? { ...r, ...patch } : r))));

  async function save() {
    setBusy(true);
    setError("");
    try {
      await api.putClients(rows);
      await refreshConfig();
      setSaved(rows.map((r) => ({ ...r })));
      setDone(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {error && <Alert>{error}</Alert>}
      <Card
        title="Clients"
        i={0}
        aside={
          <button type="button" onClick={save} disabled={!dirty || busy} className="btn btn-primary !text-white">
            <Save size={16} />
            {busy ? "Saving" : "Save changes"}
          </button>
        }
      >
        <p className="mb-6 max-w-2xl text-grey-600">
          The <strong>greeting name</strong> is how the email addresses the client. Leave it empty for &ldquo;Hi &lt;client&gt; team,&rdquo;. It applies to emails you generate from now on; emails already generated keep their greeting unless you edit it.
        </p>
        {done && <div className="mb-4"><Alert tone="info">Saved. New emails use these details.</Alert></div>}
        <ul className="divide-y divide-grey-100">
          {rows.map((c, i) => (
            <li key={c.name} className="grid gap-4 py-5 lg:grid-cols-12">
              <div className="lg:col-span-2">
                <p className="font-display text-lg font-semibold text-indigo">{c.name}</p>
                <p className="text-xs text-grey-600" title="The name is how the SEO sheet notes are matched, so it is changed in config.json">Name is fixed here</p>
              </div>
              <div className="lg:col-span-3">
                <label className="label" htmlFor={`site-${i}`}>Website (Search Console)</label>
                <input id={`site-${i}`} className="field" value={c.property} onChange={(e) => set(i, { property: e.target.value })} />
              </div>
              <div className="lg:col-span-4">
                <TagInput label="Category" values={splitTags(c.category)} onChange={(tags) => set(i, { category: joinTags(tags) })} suggestions={known} placeholder="Add a category…" />
              </div>
              <div className="lg:col-span-3">
                <label className="label" htmlFor={`greet-${i}`}>Greeting name</label>
                <input id={`greet-${i}`} className="field" value={c.contact ?? ""} maxLength={60} placeholder="e.g. Ben" onChange={(e) => set(i, { contact: e.target.value })} />
                <p className="mt-1 text-sm text-grey-600">Email starts: <strong className="text-ink">{greeting(c)}</strong></p>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
