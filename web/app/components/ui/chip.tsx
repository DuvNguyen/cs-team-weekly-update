"use client";

import { X } from "lucide-react";
import type { ReactNode } from "react";

export function Chip({ children, onRemove, removeLabel }: { children: ReactNode; onRemove?: () => void; removeLabel?: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-050 py-1 pl-3 pr-1.5 text-sm font-semibold text-brand-600">
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          aria-label={removeLabel}
          className="grid size-5 place-items-center rounded-full transition-colors duration-[var(--dur-fast)] hover:bg-brand hover:text-white"
        >
          <X size={13} strokeWidth={2.5} />
        </button>
      )}
    </span>
  );
}
