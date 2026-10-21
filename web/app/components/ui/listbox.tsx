"use client";

// Shared pieces for the two comboboxes: option list, keyboard scrolling, outside-click close.

import { Check } from "lucide-react";
import { useEffect } from "react";

export type Option = { value: string; label: string; hint?: string };

export function useOutsideClose(ref: React.RefObject<HTMLElement | null>, onClose: () => void) {
  useEffect(() => {
    const handler = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener("pointerdown", handler);
    return () => document.removeEventListener("pointerdown", handler);
  }, [ref, onClose]);
}

export function filterOptions(options: Option[], query: string) {
  const q = query.trim().toLowerCase();
  return q ? options.filter((o) => `${o.label} ${o.hint ?? ""}`.toLowerCase().includes(q)) : options;
}

export function scrollActiveIntoView(list: HTMLUListElement | null, index: number) {
  (list?.children[index] as HTMLElement | undefined)?.scrollIntoView({ block: "nearest" });
}

export function Listbox(props: {
  id: string;
  listRef: React.RefObject<HTMLUListElement | null>;
  options: Option[];
  active: number;
  isSelected: (o: Option) => boolean;
  multi?: boolean;
  onPick: (o: Option) => void;
  onHover: (i: number) => void;
  empty?: string;
}) {
  const { id, listRef, options, active, isSelected, multi, onPick, onHover, empty = "Nothing matches that." } = props;
  if (options.length === 0) return <p className="px-4 py-5 text-center text-grey-600">{empty}</p>;
  return (
    <ul ref={listRef} id={id} role="listbox" aria-multiselectable={multi} className="max-h-64 overflow-y-auto p-1.5">
      {options.map((o, i) => {
        const selected = isSelected(o);
        return (
          <li
            key={o.value}
            id={`${id}-${i}`}
            role="option"
            aria-selected={selected}
            onPointerEnter={() => onHover(i)}
            onPointerDown={(e) => e.preventDefault() /* keep focus in the input */}
            onClick={() => onPick(o)}
            className={`flex cursor-pointer items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 transition-colors duration-[var(--dur-fast)] ${
              i === active ? "bg-brand-050" : ""
            }`}
          >
            <span
              aria-hidden
              className={`grid size-5 shrink-0 place-items-center rounded-[var(--radius-xs)] ${
                multi ? `border-[1.5px] ${selected ? "border-brand bg-brand text-white" : "border-grey-400 bg-white"}` : "text-brand"
              }`}
            >
              {selected && <Check size={13} strokeWidth={3} />}
            </span>
            <span className="min-w-0 flex-1">
              <span className={`block truncate ${selected ? "font-semibold text-indigo" : ""}`}>{o.label}</span>
              {o.hint && <span className="block truncate text-sm text-grey-600">{o.hint}</span>}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export const popover =
  "absolute inset-x-0 top-full z-[200] mt-2 overflow-hidden rounded-[var(--radius-md)] border border-grey-200 bg-white shadow-[var(--shadow-md)]";
