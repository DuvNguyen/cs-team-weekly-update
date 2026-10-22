"use client";

import { useLayoutEffect, useRef, useState } from "react";
import { AlertTriangle, Info } from "lucide-react";
import type { ReactNode } from "react";

export function Badge({ tone = "neutral", children }: { tone?: "neutral" | "blue" | "sky" | "danger" | "amber"; children: ReactNode }) {
  const cls = {
    neutral: "bg-grey-100 text-grey-600",
    blue: "bg-brand-050 text-brand-600",
    sky: "bg-sky-050 text-sky-700",
    danger: "bg-danger-050 text-danger",
    amber: "bg-[#fff4d6] text-[#8a6100]",
  }[tone];
  return <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-[0.01em] ${cls}`}>{children}</span>;
}

export function Alert({ tone = "error", children }: { tone?: "error" | "info"; children: ReactNode }) {
  const Icon = tone === "error" ? AlertTriangle : Info;
  const cls = tone === "error" ? "bg-danger-050 text-danger" : "bg-brand-050 text-brand-600";
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`flex gap-3 rounded-[var(--radius-md)] px-4 py-3 ${cls}`}>
      <Icon size={20} className="mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1 break-words text-ink">{children}</div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`skeleton rounded-[var(--radius-md)] ${className}`} />;
}

/* Long text (an API error) cut to two lines with "…"; See more / See less toggles it. */
export function ExpandableAlert({ children }: { children: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [open, setOpen] = useState(false);
  const [clipped, setClipped] = useState(false);

  useLayoutEffect(() => {
    const el = ref.current;
    if (el && !open) setClipped(el.scrollHeight > el.clientHeight + 1);
  }, [children, open]);

  return (
    <Alert>
      <span ref={ref} className={`block ${open ? "" : "line-clamp-2"}`}>{children}</span>
      {(clipped || open) && (
        <button type="button" onClick={() => setOpen((o) => !o)} className="mt-1 text-sm font-semibold text-danger underline">
          {open ? "See less" : "See more"}
        </button>
      )}
    </Alert>
  );
}
