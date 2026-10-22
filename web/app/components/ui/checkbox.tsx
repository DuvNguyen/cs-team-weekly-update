"use client";

import { Check } from "lucide-react";
import type { ReactNode } from "react";

export function Checkbox({ checked, onChange, children, disabled = false }: { checked: boolean; onChange: (v: boolean) => void; children: ReactNode; disabled?: boolean }) {
  return (
    <label className={`inline-flex items-center gap-2.5 ${disabled ? "cursor-not-allowed opacity-55" : "cursor-pointer"}`}>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} className="peer sr-only" />
      <span
        aria-hidden
        className="grid size-5 place-items-center rounded-[var(--radius-xs)] border-[1.5px] border-grey-400 bg-white text-white transition-colors duration-[var(--dur-fast)] peer-checked:border-brand peer-checked:bg-brand peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-(--focus-ring)"
      >
        {checked && <Check size={13} strokeWidth={3} />}
      </span>
      <span className="text-[0.9375rem] font-medium">{children}</span>
    </label>
  );
}
