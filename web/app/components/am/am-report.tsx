"use client";

import { Download, FileText, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type AmData, type AmResult, type AmSettings } from "../../lib/api";
import { Alert, Badge } from "../ui/feedback";
import { Card } from "../ui/card";

const mondayOf = (d: Date) => {
  const m = new Date(d);
  m.setDate(m.getDate() - ((m.getDay() + 6) % 7));
  return `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, "0")}-${String(m.getDate()).padStart(2, "0")}`;
};
const lines = (text: string) => text.split("\n").map((l) => l.trim()).filter(Boolean);

/* Lines of text, one bullet per line. The parent re-keys it when a new report is generated. */
function Lines({ label, value, onChange }: { label: string; value: string[]; onChange: (v: string[]) => void }) {
  const [text, setText] = useState(value.join("\n"));
  return (
    <div>
      <label className="label">{label}</label>
      <textarea
        className="field min-h-28"
        value={text}
        placeholder="Nothing here. The CS team fills this in."
        onChange={(e) => (setText(e.target.value), onChange(lines(e.target.value)))}
      />
    </div>
  );
}

export function AmReport() {
  const [week, setWeek] = useState(() => mondayOf(new Date()));
  const [result, setResult] = useState<AmResult | null>(null);
  const [data, setData] = useState<AmData | null>(null);
  const [settings, setSettings] = useState<AmSettings | null>(null);
  const [busy, setBusy] = useState<"" | "generate" | "export" | "save">("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [gen, setGen] = useState(0);

  useEffect(() => {
    api.amSettings().then(setSettings).catch((e) => setError(e.message));
  }, []);

  async function run(kind: "generate" | "export" | "save", job: () => Promise<void>) {
    setBusy(kind);
    setError("");
    try {
      await job();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  const generate = () =>
    run("generate", async () => {
      const r = await api.amGenerate(week);
      setResult(r);
      setData(r.data);
      setGen((g) => g + 1);
    });
  const download = () => result && data && run("export", () => api.amExport(result.week_start, data));
  const saveSettings = () =>
    settings &&
    run("save", async () => {
      setSettings(await api.saveAmSettings(settings));
      setSaved(true);
    });
  const set = (patch: Partial<AmData>) => setData((d) => (d ? { ...d, ...patch } : d));
  const setS = (patch: Partial<AmSettings>) => (setSaved(false), setSettings((s) => (s ? { ...s, ...patch } : s)));

  return (
    <div className="space-y-8">
      {error && <Alert>{error}</Alert>}

      <Card title="Account Manager report" i={0}>
        <p className="mb-6 max-w-2xl text-grey-600">
          Pulls this week&rsquo;s work from SD Friday, draws the workload pictures and builds the weekly report. Anything SD Friday can&rsquo;t supply is left blank for the CS team.
        </p>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="am-week" className="label">Week (Monday to Friday)</label>
            <input id="am-week" type="date" className="field" value={week} onChange={(e) => setWeek(mondayOf(new Date(`${e.target.value}T00:00`)))} />
          </div>
          <button type="button" onClick={generate} disabled={busy !== ""} className="btn btn-primary btn-lg !text-white">
            <FileText size={18} />
            {busy === "generate" ? "Reading SD Friday…" : result ? "Generate again" : "Generate report"}
          </button>
        </div>
      </Card>

      {result && data && (
        <>
          {result.warnings.map((w) => (
            <Alert key={w} tone="info">{w}</Alert>
          ))}
          {result.idle.length > 0 && <Alert tone="info">No hours planned next week for: {result.idle.join(", ")}.</Alert>}

          <Card title="Review" i={1} aside={<Badge tone="neutral">{result.blank.length} left blank</Badge>}>
            <div className="grid gap-6 lg:grid-cols-3">
              {([["submitter", "Submitted by"], ["date_text", "Date of submission"], ["reviewer", "Reviewer"]] as const).map(([k, label]) => (
                <div key={k}>
                  <label className="label">{label}</label>
                  <input className="field" value={data[k]} onChange={(e) => set({ [k]: e.target.value })} />
                </div>
              ))}
            </div>
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <Lines key={`last-${gen}`} label="Last week" value={data.last_week} onChange={(v) => set({ last_week: v })} />
              <Lines key={`this-${gen}`} label="This week" value={data.this_week} onChange={(v) => set({ this_week: v })} />
              <Lines key={`block-${gen}`} label="Blockers" value={data.blockers} onChange={(v) => set({ blockers: v })} />
            </div>

            {(["dev", "seo"] as const).map((section) => (
              <div key={section} className="mt-8">
                <h3 className="mb-3 text-lg">{section === "dev" ? "Developers: workload" : "SEO team: workload"}</h3>
                <div className="space-y-2">
                  {result.pictures.filter((p) => p.section === section).map((p) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img key={p.name} src={p.url} alt={`${p.person}, ${p.week} week`} className="w-full max-w-3xl rounded-[var(--radius-md)]" />
                  ))}
                  {!result.pictures.some((p) => p.section === section) && <p className="text-grey-600">No people found. Check the names in the settings below.</p>}
                </div>
              </div>
            ))}

            {result.blank.length > 0 && (
              <div className="mt-8">
                <h3 className="mb-2 text-lg">Left blank for the CS team</h3>
                <ul className="list-inside list-disc text-grey-600">
                  {result.blank.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-8">
              <button type="button" onClick={download} disabled={busy !== ""} className="btn btn-primary btn-lg !text-white">
                <Download size={18} />
                {busy === "export" ? "Building…" : "Download .docx"}
              </button>
            </div>
          </Card>
        </>
      )}

      {settings && (
        <Card title="Report settings" i={2}>
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <label className="label">Submitted by</label>
              <input className="field" value={settings.submitter} onChange={(e) => setS({ submitter: e.target.value })} />
            </div>
            <div>
              <label className="label">Reviewer</label>
              <input className="field" value={settings.reviewer} onChange={(e) => setS({ reviewer: e.target.value })} />
            </div>
            <div>
              <label className="label">Developers in the workload pictures (one name per line)</label>
              <textarea className="field min-h-24" value={settings.dev_roster.join("\n")} onChange={(e) => setS({ dev_roster: lines(e.target.value) })} />
            </div>
            <div>
              <label className="label">SEO team in the workload pictures (one name per line)</label>
              <textarea className="field min-h-24" value={settings.seo_roster.join("\n")} onChange={(e) => setS({ seo_roster: lines(e.target.value) })} />
            </div>
          </div>
          <div className="mt-6 flex items-center gap-4">
            <button type="button" onClick={saveSettings} disabled={busy !== ""} className="btn btn-outline">
              <Save size={16} />
              Save settings
            </button>
            {saved && <span className="text-sm text-grey-600">Saved. Generate again to use them.</span>}
          </div>
        </Card>
      )}
    </div>
  );
}
