"use client";

import { Pencil, RotateCcw } from "lucide-react";
import { api, type ClientRow, type Job } from "../../lib/api";
import { Checkbox } from "../ui/checkbox";
import { Badge, ExpandableAlert, Skeleton } from "../ui/feedback";
import { Stats } from "./stats";

export function ClientCard(props: {
  i: number;
  job: Job;
  c: ClientRow;
  text: string;
  onOpen: () => void;
  onInclude: (v: boolean) => void;
  onRetry: () => void;
}) {
  const { i, job, c, text, onOpen, onInclude, onRetry } = props;
  const openable = c.status === "ok";
  const badge = {
    pending: <Badge>Waiting</Badge>,
    running: <Badge tone="blue">Working</Badge>,
    ok: <Badge tone="sky">Ready</Badge>,
    failed: <Badge tone="danger">Failed</Badge>,
  }[c.status];

  return (
    <section
      role={openable ? "button" : undefined}
      tabIndex={openable ? 0 : undefined}
      aria-label={openable ? `Open email for ${c.name}` : undefined}
      onClick={openable ? onOpen : undefined}
      onKeyDown={(e) => {
        if (openable && e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          onOpen();
        }
      }}
      className={`card rise p-8 transition-[opacity,box-shadow] duration-[var(--dur-base)] ${openable ? "cursor-pointer hover:shadow-[var(--shadow-md)]" : ""} ${c.status === "ok" && !c.include ? "opacity-55" : ""}`}
      style={{ ["--i" as string]: i }}
    >
      <header className="mb-6 flex flex-wrap items-start justify-between gap-x-6 gap-y-2">
        <div>
          <h2 className="flex flex-wrap items-center gap-3 text-2xl">
            {c.name}
            {badge}
          </h2>
          <p className="text-sm text-grey-600">{c.property}</p>
        </div>
        {c.status === "ok" && (
          <span onClick={(e) => e.stopPropagation()}>
            <Checkbox checked={c.include} onChange={onInclude}>
              Include in file
            </Checkbox>
          </span>
        )}
      </header>

      {(c.status === "pending" || c.status === "running") && (
        <div className="grid gap-6 lg:grid-cols-12">
          <Skeleton className="aspect-[12/5.2] lg:col-span-7" />
          <div className="space-y-3 lg:col-span-5">
            <Skeleton className="h-4 w-full !rounded-full" />
            <Skeleton className="h-4 w-11/12 !rounded-full" />
            <Skeleton className="h-4 w-4/5 !rounded-full" />
            <Skeleton className="h-4 w-2/3 !rounded-full" />
          </div>
        </div>
      )}

      {c.status === "failed" && (
        <div className="max-w-2xl space-y-4">
          <ExpandableAlert>{c.error}</ExpandableAlert>
          <button onClick={onRetry} className="btn btn-outline">
            <RotateCcw size={16} />
            Retry
          </button>
        </div>
      )}

      {c.status === "ok" && c.totals && (
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`${api.chartUrl(job.id, c.name)}?t=${c.totals.clicks}-${c.totals.impressions}`}
              alt={`Clicks and impressions for ${c.name}`}
              className="w-full rounded-[var(--radius-md)] border border-grey-200 bg-white"
            />
            {c.prev_totals && <Stats now={c.totals} prev={c.prev_totals} />}
          </div>
          <div className="flex flex-col lg:col-span-7">
            <span className="label">Email to the client{c.style_name ? <span className="font-normal text-grey-600"> &middot; {c.style_name}</span> : null}</span>
            <p className="line-clamp-6 flex-1 whitespace-pre-line leading-relaxed text-grey-600">{text}</p>
            <span className="mt-3 inline-flex items-center gap-1.5 self-start text-sm font-semibold text-brand">
              <Pencil size={14} />
              Open to edit or regenerate
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
