"use client";

import { ChevronDown, Search } from "lucide-react";
import { useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Chip } from "./chip";
import { Listbox, filterOptions, popover, scrollActiveIntoView, useOutsideClose, type Option } from "./listbox";

/* Multi-select with removable chips. */
export function MultiCombobox(props: {
  label: string;
  values: string[];
  onChange: (v: string[]) => void;
  options: Option[];
  placeholder?: string;
}) {
  const { label, values, onChange, options, placeholder } = props;
  const uid = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  useOutsideClose(rootRef, () => setOpen(false));

  const filtered = useMemo(() => filterOptions(options, query), [options, query]);
  const chosen = options.filter((o) => values.includes(o.value));

  function toggle(o: Option) {
    onChange(values.includes(o.value) ? values.filter((v) => v !== o.value) : [...values, o.value]);
    setQuery("");
  }
  function move(next: number) {
    const i = Math.min(filtered.length - 1, Math.max(0, next));
    setActive(i);
    scrollActiveIntoView(listRef.current, i);
  }
  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (open) move(active + (e.key === "ArrowDown" ? 1 : -1));
      else setOpen(true);
    } else if (open && e.key === "Enter") {
      e.preventDefault();
      if (filtered[active]) toggle(filtered[active]);
    } else if (open && e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    } else if (e.key === "Backspace" && !query && values.length) {
      onChange(values.slice(0, -1));
    } else if (e.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <label htmlFor={`${uid}-input`} className="label">{label}</label>
      <div
        className="field flex cursor-text items-start gap-2 !pr-2 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo"
        onClick={() => {
          inputRef.current?.focus();
          setOpen(true);
        }}
      >
        <div className="flex max-h-28 min-w-0 flex-1 flex-wrap items-center gap-1.5 overflow-y-auto">
          {chosen.map((o) => (
            <Chip key={o.value} onRemove={() => onChange(values.filter((v) => v !== o.value))} removeLabel={`Remove ${o.label}`}>
              {o.label}
            </Chip>
          ))}
          <span className="relative min-w-32 flex-1">
            <Search size={15} aria-hidden className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 text-grey-400" />
            <input
              ref={inputRef}
              id={`${uid}-input`}
              role="combobox"
              aria-expanded={open}
              aria-controls={`${uid}-list`}
              aria-autocomplete="list"
              aria-activedescendant={open && filtered[active] ? `${uid}-list-${active}` : undefined}
              autoComplete="off"
              placeholder={chosen.length ? "Search to add…" : placeholder}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setActive(0);
                setOpen(true);
              }}
              onKeyDown={onKey}
              className="w-full bg-transparent py-1 pl-6 outline-none placeholder:text-grey-400"
            />
          </span>
        </div>
        <button
          type="button"
          aria-label={open ? "Close the list" : "Open the list"}
          onClick={(e) => {
            e.stopPropagation();
            setOpen(!open);
          }}
          className="grid size-8 shrink-0 place-items-center rounded-full border border-grey-200 text-grey-600 transition-colors duration-[var(--dur-fast)] hover:bg-brand-050 hover:text-brand"
        >
          <ChevronDown size={18} className={`transition-transform duration-[var(--dur-base)] ${open ? "rotate-180" : ""}`} />
        </button>
      </div>
      {open && (
        <div className={popover}>
          <div className="flex items-center justify-between border-b border-grey-200 px-4 py-2.5 text-sm">
            <span className="text-xs font-medium text-grey-600">{values.length}/{options.length} selected</span>
            <span className="flex gap-4">
              <button type="button" className="btn-link" onPointerDown={(e) => e.preventDefault()} onClick={() => onChange(options.map((o) => o.value))}>
                Select all
              </button>
              <button type="button" className="btn-link" onPointerDown={(e) => e.preventDefault()} onClick={() => onChange([])}>
                Clear
              </button>
            </span>
          </div>
          <Listbox
            id={`${uid}-list`}
            listRef={listRef}
            options={filtered}
            active={active}
            multi
            isSelected={(o) => values.includes(o.value)}
            onPick={toggle}
            onHover={setActive}
          />
        </div>
      )}
    </div>
  );
}
