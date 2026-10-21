import { Check } from "lucide-react";
import Link from "next/link";

/* Setup is /setup; Generate and Review are the same page (/report) at different moments. */
export function Stepper({ step, hasReport }: { step: number; hasReport: boolean }) {
  const steps = [
    { name: "Setup", href: "/setup" },
    { name: "Generate", href: "/report" },
    { name: "Review", href: "/report" },
  ];
  return (
    <nav aria-label="Progress">
      <ol className="inline-flex gap-1 rounded-full bg-white/10 p-1">
        {steps.map(({ name, href }, i) => {
          const n = i + 1;
          const state = n < step ? "done" : n === step ? "current" : "todo";
          const enabled = n === 1 || hasReport;
          const cls = `flex items-center gap-2 rounded-full px-4 py-1.5 text-[0.9375rem] font-semibold !no-underline transition-colors duration-[var(--dur-fast)] ${
            state === "current"
              ? "bg-white !text-indigo shadow-[var(--shadow-xs)]"
              : `${state === "done" ? "!text-white/85" : "!text-white/45"} ${enabled ? "hover:bg-white/10 hover:!text-white" : ""}`
          }`;
          const inner = (
            <>
              {state === "done" ? <Check size={14} strokeWidth={3} className="text-sky" /> : <span className="font-display text-xs">{n}</span>}
              {name}
            </>
          );
          return (
            <li key={name}>
              {enabled && state !== "current" ? (
                <Link href={href} className={cls}>{inner}</Link>
              ) : (
                <span aria-current={state === "current" ? "step" : undefined} className={cls}>{inner}</span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
