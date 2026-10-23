"use client";

import { Plus } from "lucide-react";
import { useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Chip } from "./chip";
import { Listbox, filterOptions, popover, scrollActiveIntoView, useOutsideClose, type Option } from "./listbox";

/* "Furniture, Interior Design" is stored as one string; as tags it is two. */
export const splitTags = (s: string) => s.split(",").map((t) => t.trim()).filter(Boolean);
export const joinTags = (tags: string[]) => tags.join(", ");

/* Free-text tags as removable chips. Type and press Enter or comma to add; suggestions come from tags already in use. */
export function TagInput(props: {
  label: string;
  values: string[];
  onChange: (v: string[]) => void;
  suggestions?: string[];
  placeholder?: string;
}) {
  const { label, values, onChange, suggestions = [], placeholder } = props;
  const uid = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const has = (list: string[], t: string) => list.some((v) => v.toLowerCase() === t.toLowerCase());

  function add(raw: string) {
    const next = [...values];
    for (const t of splitTags(raw)) if (!has(next, t)) next.push(t);
    if (next.length !== values.length) onChange(next);
    setQuery("");
    setActive(0);
  }

  useOutsideClose(rootRef, () => {
    setOpen(false);
    if (query.trim()) add(query);        // typed text that was never confirmed still counts
  });

  const options = useMemo<Option[]>(() => {
    const pool = filterOptions(suggestions.filter((s) => !has(values, s)).map((s) => ({ value: s, label: s })), query);
    const q = query.trim();
    return q && !has(suggestions, q) && !has(values, q) ? [...pool, { value: q, label: `Add “${q}”` }] : pool;
  }, [suggestions, values, query]);

  function move(next: number) {
    const i = Math.min(options.length - 1, Math.max(0, next));
    setActive(i);
    scrollActiveIntoView(listRef.current, i);
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (open) move(active + (e.key === "ArrowDown" ? 1 : -1));
      else setOpen(true);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (open && options[active]) add(options[active].value);
      else if (query.trim()) add(query);
    } else if (e.key === "," || e.key === "Tab") {
      if (query.trim()) {
        if (e.key === ",") e.preventDefault();
        add(query);
      }
      if (e.key === "Tab") setOpen(false);
    } else if (e.key === "Escape" && open) {
      e.preventDefault();
      setOpen(false);
    } else if (e.key === "Backspace" && !query && values.length) {
      onChange(values.slice(0, -1));
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <label htmlFor={`${uid}-input`} className="label">{label}</label>
      <div
        className="field group flex cursor-text flex-wrap items-center gap-1.5 !py-2 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo"
        onClick={() => {
          inputRef.current?.focus();
          setOpen(true);
        }}
      >
        {values.map((v) => (
          <Chip key={v} onRemove={() => onChange(values.filter((x) => x !== v))} removeLabel={`Remove ${v}`}>
            {v}
          </Chip>
        ))}
        {/* with tags it takes no room until you click in */}
        <span className={`relative ${values.length ? "w-0 min-w-0 overflow-hidden group-focus-within:w-auto group-focus-within:min-w-24 group-focus-within:flex-1" : "min-w-24 flex-1"}`}>
          <Plus size={14} aria-hidden className={`pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 text-grey-400 ${values.length ? "opacity-0 group-focus-within:opacity-100" : ""}`} />
          <input
            ref={inputRef}
            id={`${uid}-input`}
            role="combobox"
            aria-expanded={open}
            aria-controls={`${uid}-list`}
            aria-autocomplete="list"
            aria-activedescendant={open && options[active] ? `${uid}-list-${active}` : undefined}
            autoComplete="off"
            placeholder={values.length ? "Add a tag…" : placeholder}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKey}
            className={`w-full bg-transparent py-0.5 pl-5 outline-none ${values.length ? "placeholder:text-transparent focus:placeholder:text-grey-400" : "placeholder:text-grey-400"}`}
          />
        </span>
      </div>
      {open && options.length > 0 && (
        <div className={popover}>
          <Listbox id={`${uid}-list`} listRef={listRef} options={options} active={active} multi={false} isSelected={() => false} onPick={(o) => add(o.value)} onHover={setActive} />
        </div>
      )}
    </div>
  );
}
