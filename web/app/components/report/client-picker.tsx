"use client";

import { Check, Search } from "lucide-react";
import { useState } from "react";
import type { Config } from "../../lib/api";

/* Every client visible at once: click a row to include or drop it. */
export function ClientPicker({
  clients,
  picked,
  onChange,
}: {
  clients: Config["clients"];
  picked: string[];
  onChange: (names: string[]) => void;
}) {
  const [q, setQ] = useState("");
  const shown = clients.filter((c) => `${c.name} ${c.category ?? ""}`.toLowerCase().includes(q.trim().toLowerCase()));
  const all = clients.length > 0 && picked.length === clients.length;

  function toggle(name: string) {
    onChange(clients.map((c) => c.name).filter((n) => (n === name ? !picked.includes(n) : picked.includes(n))));
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="field flex flex-1 items-center gap-2 !py-2" style={{ minWidth: "12rem" }}>
          <Search size={16} className="text-grey-400" aria-hidden />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Filter clients…"
            aria-label="Filter clients"
            className="w-full bg-transparent outline-none"
          />
        </div>
        <button type="button" className="btn-link text-sm" onClick={() => onChange(clients.map((c) => c.name))} disabled={all}>
          Select all
        </button>
        <button type="button" className="btn-link text-sm" onClick={() => onChange([])} disabled={picked.length === 0}>
          Clear
        </button>
      </div>

      <ul className="grid gap-2 sm:grid-cols-2" aria-label="Clients">
        {shown.map((c) => {
          const on = picked.includes(c.name);
          return (
            <li key={c.name}>
              <button
                type="button"
                role="checkbox"
                aria-checked={on}
                onClick={() => toggle(c.name)}
                className={`flex w-full items-center gap-3 rounded-[var(--radius-sm)] border px-3.5 py-2.5 text-left transition-colors duration-[var(--dur-fast)] ${
                  on ? "border-brand bg-brand-050" : "border-grey-200 bg-white hover:border-grey-400"
                }`}
              >
                <span
                  aria-hidden
                  className={`grid size-5 shrink-0 place-items-center rounded-[var(--radius-xs)] border-[1.5px] text-white ${
                    on ? "border-brand bg-brand" : "border-grey-400 bg-white"
                  }`}
                >
                  {on && <Check size={13} strokeWidth={3} />}
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-[0.9375rem] font-semibold text-indigo">{c.name}</span>
                  {c.category && <span className="block truncate text-xs text-grey-600">{c.category}</span>}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {shown.length === 0 && <p className="py-4 text-center text-sm text-grey-600">No client matches &ldquo;{q}&rdquo;.</p>}
    </div>
  );
}
