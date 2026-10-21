"use client";

import { Download, Save, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type AmData, type AmItem, type AmPicture, type AmResult, type AmSettings, type AmTemplate } from "../../lib/api";
import { Alert, Badge } from "../ui/feedback";
import { Card } from "../ui/card";

const ymd = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const mondayOf = (d: Date) => {
  const m = new Date(d);
  m.setDate(m.getDate() - ((m.getDay() + 6) % 7));
  return ymd(m);
};
const fridayText = (monday: string) => {
  const f = new Date(`${monday}T00:00`);
  f.setDate(f.getDate() + 4);
  return `${String(f.getDate()).padStart(2, "0")}/${String(f.getMonth() + 1).padStart(2, "0")}/${String(f.getFullYear()).slice(2)}`;
};
const lines = (text: string) => text.split("\n").map((l) => l.trim()).filter(Boolean);
const EMPTY: AmData = { submitter: "", reviewer: "", date_text: "", dev_pictures: [], seo_pictures: [], last_week: [], this_week: [], blockers: [], answers: {} };

/* One bullet per line. Re-keyed by the parent when SD Friday fills it, so it picks up the new text. */
function Lines({ label, value, onChange, auto }: { label: string; value: string[]; onChange: (v: string[]) => void; auto: boolean }) {
  const [text, setText] = useState(value.join("\n"));
  return (
    <div>
      <label className="label flex items-center gap-2">
        {label}
        {auto && <Badge tone="sky">From SD Friday</Badge>}
      </label>
      <textarea className="field min-h-24" value={text} onChange={(e) => (setText(e.target.value), onChange(lines(e.target.value)))} />
    </div>
  );
}

function Pictures({ pictures, week }: { pictures: AmPicture[]; week: string }) {
  if (!pictures.length) return null;
  return (
    <div className="space-y-2">
      <Badge tone="sky">From SD Friday</Badge>
      {pictures.map((p) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img key={`${week}-${p.name}`} src={p.url} alt={`${p.person}, ${p.week} week`} className="w-full max-w-3xl rounded-[var(--radius-md)]" />
      ))}
    </div>
  );
}

export function AmReport() {
  const [week, setWeek] = useState(() => mondayOf(new Date()));
  const [template, setTemplate] = useState<AmTemplate | null>(null);
  const [settings, setSettings] = useState<AmSettings | null>(null);
  const [data, setData] = useState<AmData>(EMPTY);
  const [result, setResult] = useState<AmResult | null>(null);
  const [busy, setBusy] = useState<"" | "fill" | "export" | "save">("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [gen, setGen] = useState(0);

  useEffect(() => {
    Promise.all([api.amTemplate(), api.amSettings()])
      .then(([t, s]) => {
        setTemplate(t);
        setSettings(s);
        setData((d) => ({ ...d, submitter: s.submitter, reviewer: s.reviewer, date_text: fridayText(week) }));
      })
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once
  }, []);

  async function run(kind: "fill" | "export" | "save", job: () => Promise<void>) {
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

  // New week: the pictures belong to the old one, so drop them. The rest of the form is kept.
  function changeWeek(monday: string) {
    setWeek(monday);
    setResult(null);
    setData((d) => ({ ...d, dev_pictures: [], seo_pictures: [], date_text: fridayText(monday) }));
  }

  const fill = () =>
    run("fill", async () => {
      const r = await api.amGenerate(week);
      setResult(r);
      // Only what SD Friday knows. The names, date and every typed answer stay as they are.
      setData((d) => ({ ...d, dev_pictures: r.data.dev_pictures, seo_pictures: r.data.seo_pictures, last_week: r.data.last_week, this_week: r.data.this_week, blockers: r.data.blockers }));
      setGen((g) => g + 1);
    });
  const download = () => run("export", () => api.amExport(result?.week_start ?? week, data));
  const saveSettings = () =>
    settings &&
    run("save", async () => {
      setSettings(await api.saveAmSettings(settings));
      setSaved(true);
    });

  const set = (patch: Partial<AmData>) => setData((d) => ({ ...d, ...patch }));
  const setAnswer = (key: string, v: string) => setData((d) => ({ ...d, answers: { ...d.answers, [key]: v } }));
  const setS = (patch: Partial<AmSettings>) => (setSaved(false), setSettings((s) => (s ? { ...s, ...patch } : s)));
  const filled = result !== null;
  const picturesFor = (answer: string | null) => (answer === "dev_pictures" ? "dev" : answer === "seo_pictures" ? "seo" : null);

  // A plain function (not a component) so the fields keep focus while typing.
  function question(item: AmItem) {
    const section = picturesFor(item.answer);
    return (
      <div key={item.key} className="space-y-3 border-t border-grey-100 py-5 first:border-t-0">
        <p>
          <strong className="text-indigo">{item.label}:</strong> {item.text}
        </p>
        {item.answer === "client_lists" ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Lines key={`last-${gen}`} label={item.lists?.[0] ?? "Last week:"} value={data.last_week} onChange={(v) => set({ last_week: v })} auto={filled} />
            <Lines key={`this-${gen}`} label={item.lists?.[1] ?? "This week:"} value={data.this_week} onChange={(v) => set({ this_week: v })} auto={filled} />
          </div>
        ) : item.answer === "blockers" ? (
          <Lines key={`block-${gen}`} label="Blockers (one per line)" value={data.blockers} onChange={(v) => set({ blockers: v })} auto={filled} />
        ) : (
          <>
            {section && result && <Pictures pictures={result.pictures.filter((p) => p.section === section)} week={result.week_start} />}
            <textarea
              className="field min-h-20"
              aria-label={`${item.label} answer`}
              placeholder={section ? "Notes (optional)" : "Type your answer"}
              value={data.answers[item.key] ?? ""}
              onChange={(e) => setAnswer(item.key, e.target.value)}
            />
          </>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {error && <Alert>{error}</Alert>}

      <Card title="Account Manager report" i={0}>
        <p className="mb-6 max-w-2xl text-grey-600">
          Fill the form by hand, or press <strong>Fill from SD Friday</strong> to add what it knows: the client bullets, blockers and workload pictures. Anything left empty is highlighted in the document for you to complete.
        </p>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="am-week" className="label">Week (Monday to Friday)</label>
            <input id="am-week" type="date" className="field" value={week} onChange={(e) => e.target.value && changeWeek(mondayOf(new Date(`${e.target.value}T00:00`)))} />
          </div>
          <button type="button" onClick={fill} disabled={busy !== ""} className="btn btn-outline btn-lg">
            <Wand2 size={18} />
            {busy === "fill" ? "Reading SD Friday…" : filled ? "Fill again" : "Fill from SD Friday"}
          </button>
          <button type="button" onClick={download} disabled={busy !== "" || !template} className="btn btn-primary btn-lg !text-white">
            <Download size={18} />
            {busy === "export" ? "Building…" : "Download .docx"}
          </button>
        </div>
      </Card>

      {result?.warnings.map((w) => (
        <Alert key={w} tone="info">{w}</Alert>
      ))}
      {result && result.idle.length > 0 && <Alert tone="info">No hours planned next week for: {result.idle.join(", ")}.</Alert>}

      {template && (
        <Card title="Report" i={1}>
          <div className="grid gap-4 lg:grid-cols-3">
            {([["submitter", "Submitted by"], ["date_text", "Date of submission"], ["reviewer", "Reviewer"]] as const).map(([k, label]) => (
              <div key={k}>
                <label className="label">{label}</label>
                <input className="field" value={data[k]} onChange={(e) => set({ [k]: e.target.value })} />
              </div>
            ))}
          </div>
          {template.sections.map((section) => (
            <div key={section.heading} className="mt-8">
              <h3 className="border-b border-brand pb-1 text-xl text-indigo">{section.heading}</h3>
              {section.subsections.map((sub, i) => (
                <div key={sub.heading ?? i} className="mt-4">
                  {sub.heading && <h4 className="text-lg text-brand-600">{sub.heading}</h4>}
                  <p className="mb-1 text-sm italic text-grey-600">{sub.objective}</p>
                  {sub.items.map(question)}
                </div>
              ))}
            </div>
          ))}
        </Card>
      )}

      {settings && (
        <Card title="Report settings" i={2}>
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <label className="label">Submitted by (default)</label>
              <input className="field" value={settings.submitter} onChange={(e) => setS({ submitter: e.target.value })} />
            </div>
            <div>
              <label className="label">Reviewer (default)</label>
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
            {saved && <span className="text-sm text-grey-600">Saved. Press Fill from SD Friday again to use the new names.</span>}
          </div>
        </Card>
      )}
    </div>
  );
}
