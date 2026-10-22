"use client";

import { ArrowLeft, ArrowRight, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, type Config, type Job, type Voice } from "../../lib/api";
import { addDays } from "../../lib/period";
import { Card } from "../ui/card";
import { Combobox } from "../ui/combobox";
import { Alert, Skeleton } from "../ui/feedback";
import { ClientPicker } from "./client-picker";

/* Step 1: period, notes tab, clients. */
export function Setup({ config, hasReport, onBack, onStart }: { config: Config; hasReport: boolean; onBack: () => void; onStart: (j: Job) => void }) {
  const [start, setStart] = useState(config.period.start);
  const [end, setEnd] = useState(config.period.end);
  const [tab, setTab] = useState(config.seo_sheet_tab);
  const [tabs, setTabs] = useState<string[] | null>(null);
  const [tabsError, setTabsError] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const [voice, setVoice] = useState<Voice | null>(null);
  const [styleId, setStyleId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Search Console's newest day with data (the same end its own "7 days" uses). Unknown until it loads.
  const [latest, setLatest] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);
  const [staleTab, setStaleTab] = useState("");

  useEffect(() => {
    api
      .period()
      .then((r) => {
        setLatest(r.end);
        if (!touched) {
          setStart(addDays(r.end, -13));
          setEnd(r.end);
        }
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    api.voice().then((v) => {
      setVoice(v);
      setStyleId((cur) => cur || v.default_id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    api
      .tabs()
      .then((r) => {
        setTabs(r.tabs);
        // The saved default can point at a tab that has since been renamed or removed: say so, and don't send it.
        setTab((cur) => {
          if (cur && !r.tabs.includes(cur)) {
            setStaleTab(cur);
            return "";
          }
          return cur;
        });
      })
      .catch((e) => setTabsError(e.message));
  }, []);

  // Monday to Friday of the week we're standing on (local date).
  const thisWeek = useMemo(() => {
    const t = new Date();
    const today = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`;
    const monday = addDays(today, -((t.getDay() + 6) % 7));
    return { start: monday, end: addDays(monday, 4) };
  }, []);
  const presets = [
    { label: "This week", range: thisWeek },
    { label: "Last 7 days", days: 7 },
    { label: "Last 14 days", days: 14 },
    { label: "Last 30 days", days: 30 },
  ];
  const tabOptions = useMemo(
    () => [{ value: "", label: "No notes (numbers only)" }, ...(tabs ?? []).map((t) => ({ value: t, label: t }))],
    [tabs],
  );
  const valid = start && end && start <= end && picked.length > 0;

  async function go() {
    setBusy(true);
    setError("");
    try {
      onStart(await api.startJob({ tab, start, end, style_id: styleId || undefined, clients: config.clients.map((c) => c.name).filter((n) => picked.includes(n)) }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      // This page stays alive in the background while the report is open, so a stuck "Starting" would still be here on "Start over".
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      {hasReport && (
        <div className="card flex flex-wrap items-center justify-between gap-3 px-6 py-4">
          <span className="text-grey-600">You have a report in progress. Generating again replaces it.</span>
          <button type="button" onClick={onBack} className="btn btn-outline">
            <ArrowLeft size={16} />
            Back to report
          </button>
        </div>
      )}
      {config.demo && <Alert tone="info">Demo mode: the numbers are made up and nothing is sent to Google.</Alert>}

      <div className="grid items-start gap-8 lg:grid-cols-12">
        <div className="space-y-8 lg:col-span-5">
          <Card title="Report period" n={1} i={0}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="from" className="label">From</label>
                <input id="from" type="date" value={start} onChange={(e) => {
                    setTouched(true);
                    setStart(e.target.value);
                  }} className="field" />
              </div>
              <div>
                <label htmlFor="to" className="label">To</label>
                <input id="to" type="date" value={end} onChange={(e) => {
                    setTouched(true);
                    setEnd(e.target.value);
                  }} className="field" />
              </div>
            </div>
            <p className="mb-2 mt-5 text-sm font-semibold text-indigo">Or pick a shortcut</p>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Period presets">
              {presets.map((p) => {
                const last = latest ?? config.period.end;
                const s = p.range ? p.range.start : addDays(last, -(p.days - 1));
                const e = p.range ? p.range.end : last;
                const on = start === s && end === e;
                return (
                  <button
                    key={p.label}
                    type="button"
                    aria-pressed={on}
                    onClick={() => {
                      setTouched(true);
                      setStart(s);
                      setEnd(e);
                    }}
                    className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors duration-[var(--dur-fast)] ${
                      on ? "bg-brand text-white" : "bg-brand-050 text-brand-600 hover:bg-brand-100"
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
            {latest && end > latest && (
              <div className="mt-5">
                <Alert tone="info">
                  Search Console has no data after {latest}, so this report would be missing days.{" "}
                  <button
                    type="button"
                    className="btn-link"
                    onClick={() => {
                      setTouched(true);
                      setStart(addDays(latest, -(Math.round((Date.parse(end) - Date.parse(start)) / 86400000))));
                      setEnd(latest);
                    }}
                  >
                    End on {latest}
                  </button>
                </Alert>
              </div>
            )}
            <p className="mt-5 text-sm text-grey-600">
              {latest
                ? `Search Console's latest data is ${latest}, so the shortcuts end there, same as Search Console's own date picker. `
                : "Checking Search Console for the latest day with data. "}
              The window is compared with the same number of days before it.
            </p>
          </Card>

          <Card title="SEO team notes" n={2} i={1}>
            {tabs ? (
              <>
                <Combobox label="Sheet tab" value={tab} onChange={setTab} options={tabOptions} placeholder="Search tabs…" />
                <p className="mt-2 text-sm text-grey-600">Click the box and choose this period&rsquo;s tab. Type to search.</p>
                {staleTab && !tab && (
                  <div className="mt-3"><Alert>The saved tab &ldquo;{staleTab}&rdquo; is no longer in the sheet. Pick this period&rsquo;s tab.</Alert></div>
                )}
                {!tab && (
                  <div className="mt-3"><Alert tone="info">No tab chosen: the emails will use Search Console numbers only, without the SEO team&rsquo;s notes or the Trends/News column.</Alert></div>
                )}
              </>
            ) : tabsError ? (
              <>
                <label htmlFor="tab" className="label">Sheet tab</label>
                <input id="tab" value={tab} onChange={(e) => setTab(e.target.value)} placeholder="e.g. 12/10-23/10" className="field" />
                <p className="mt-2 text-sm text-danger">Could not load the tab list ({tabsError}). Type the tab name instead.</p>
              </>
            ) : (
              <>
                <span className="label">Sheet tab</span>
                <Skeleton className="h-[46px]" />
              </>
            )}
          </Card>

          <Card title="Email style" n={3} i={2}>
            {voice ? (
              <>
                <Combobox
                  label="Writing style"
                  value={styleId}
                  onChange={setStyleId}
                  options={voice.styles.map((x) => ({ value: x.id, label: x.name, hint: x.id === voice.default_id ? "Default" : undefined }))}
                  placeholder="Choose a style…"
                />
                <p className="mt-2 text-sm text-grey-600">How Gemini writes the emails. You can switch it per client when you regenerate. Manage styles under Voice rules.</p>
              </>
            ) : (
              <>
                <span className="label">Writing style</span>
                <Skeleton className="h-[46px]" />
              </>
            )}
          </Card>
        </div>

        <div className="lg:col-span-7">
          <Card title="Clients" n={4} i={3} aside={<span className="text-sm font-semibold text-grey-600">{picked.length} of {config.clients.length}</span>}>
            <ClientPicker clients={config.clients} picked={picked} onChange={setPicked} />
            <p className="mt-3 text-sm text-grey-600">Click a client to include it in the report.</p>
            {picked.length === 0 && (
              <div className="mt-5 flex flex-col items-center gap-3 rounded-[var(--radius-md)] border border-dashed border-grey-200 px-6 py-8 text-center">
                <Users size={28} className="text-grey-400" />
                <p className="text-grey-600">No clients yet. Pick at least one to build a report.</p>
                <button type="button" className="btn btn-outline" onClick={() => setPicked(config.clients.map((c) => c.name))}>
                  Select all clients
                </button>
              </div>
            )}
          </Card>

          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <button type="button" disabled={!valid || busy} onClick={go} className="btn btn-primary btn-lg">
              {busy ? "Starting" : "Generate previews"}
              <ArrowRight size={18} />
            </button>
            <span className="text-sm text-grey-600">
              {picked.length} {picked.length === 1 ? "client" : "clients"} &middot; {start} to {end}
            </span>
          </div>
          {error && <div className="mt-4"><Alert>{error}</Alert></div>}
        </div>
      </div>
    </div>
  );
}
