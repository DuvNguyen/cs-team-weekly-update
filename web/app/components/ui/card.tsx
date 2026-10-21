import type { ReactNode } from "react";

export function Card({ title, n, aside, children, i = 0 }: { title: string; n?: number; aside?: ReactNode; children: ReactNode; i?: number }) {
  return (
    <section className="card rise p-8" style={{ ["--i" as string]: i }}>
      <header className="mb-6 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-3 text-2xl">
          {n !== undefined && (
            <span className="grid size-8 place-items-center rounded-full bg-brand-050 font-display text-sm font-semibold text-brand-600">{n}</span>
          )}
          {title}
        </h2>
        {aside}
      </header>
      {children}
    </section>
  );
}
