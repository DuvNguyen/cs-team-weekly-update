import { AlertTriangle, Info } from "lucide-react";
import type { ReactNode } from "react";

export function Badge({ tone = "neutral", children }: { tone?: "neutral" | "blue" | "sky" | "danger"; children: ReactNode }) {
  const cls = {
    neutral: "bg-grey-100 text-grey-600",
    blue: "bg-brand-050 text-brand-600",
    sky: "bg-sky-050 text-sky-700",
    danger: "bg-danger-050 text-danger",
  }[tone];
  return <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-[0.01em] ${cls}`}>{children}</span>;
}

export function Alert({ tone = "error", children }: { tone?: "error" | "info"; children: ReactNode }) {
  const Icon = tone === "error" ? AlertTriangle : Info;
  const cls = tone === "error" ? "bg-danger-050 text-danger" : "bg-brand-050 text-brand-600";
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`flex gap-3 rounded-[var(--radius-md)] px-4 py-3 ${cls}`}>
      <Icon size={20} className="mt-0.5 shrink-0" />
      <div className="text-ink">{children}</div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`skeleton rounded-[var(--radius-md)] ${className}`} />;
}
