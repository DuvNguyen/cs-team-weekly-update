import type { Totals } from "../../lib/api";

export function Stats({ now, prev }: { now: Totals; prev: Totals }) {
  const pct = (a: number, b: number) => (b ? `${a >= b ? "+" : "-"}${Math.abs(((a - b) / b) * 100).toFixed(0)}%` : "n/a");
  const tone = (good: boolean | null) => (good === null ? "text-grey-600" : good ? "text-sky-700" : "text-danger");
  const p = Number(now.position);
  const pp = Number(prev.position);
  const items = [
    { label: "Clicks", value: now.clicks.toLocaleString(), delta: pct(now.clicks, prev.clicks), good: now.clicks === prev.clicks ? null : now.clicks > prev.clicks },
    { label: "Impressions", value: now.impressions.toLocaleString(), delta: pct(now.impressions, prev.impressions), good: now.impressions === prev.impressions ? null : now.impressions > prev.impressions },
    { label: "Avg position", value: now.position, delta: `was ${prev.position}`, good: p === pp ? null : p < pp },
  ];
  return (
    <dl className="grid grid-cols-3 gap-3">
      {items.map((s) => (
        <div key={s.label} className="rounded-[var(--radius-md)] bg-grey-50 px-4 py-3">
          <dt className="overline">{s.label}</dt>
          <dd className="font-display text-2xl font-semibold text-indigo">{s.value}</dd>
          <dd className={`text-sm font-semibold ${tone(s.good)}`}>{s.delta}</dd>
        </div>
      ))}
    </dl>
  );
}
