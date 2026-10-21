"use client";

import { ChevronDown } from "lucide-react";
import { useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Listbox, filterOptions, popover, scrollActiveIntoView, useOutsideClose, type Option } from "./listbox";

/* Single-select, searchable. */
export function Combobox(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Option[];
  placeholder?: string;
}) {
  const { label, value, onChange, options, placeholder } = props;
  const uid = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  useOutsideClose(rootRef, () => setOpen(false));

  const selected = options.find((o) => o.value === value);
  const filtered = useMemo(() => filterOptions(options, query), [options, query]);

  function openList() {
    if (open) return;
    setQuery("");
    setActive(Math.max(0, options.findIndex((o) => o.value === value)));
    setOpen(true);
  }
  function move(next: number) {
    const i = Math.min(filtered.length - 1, Math.max(0, next));
    setActive(i);
    scrollActiveIntoView(listRef.current, i);
  }
  function pick(o: Option) {
    onChange(o.value);
    setOpen(false);
    setQuery("");
  }
  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    const handled = () => e.preventDefault();
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      handled();
      if (open) move(active + (e.key === "ArrowDown" ? 1 : -1));
      else openList();
    } else if (open && e.key === "Home") {
      handled();
      move(0);
    } else if (open && e.key === "End") {
      handled();
      move(filtered.length - 1);
    } else if (open && e.key === "Enter") {
      handled();
      if (filtered[active]) pick(filtered[active]);
    } else if (open && e.key === "Escape") {
      handled();
      setOpen(false);
    } else if (e.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <label htmlFor={`${uid}-input`} className="label">{label}</label>
      <div className="relative">
        <input
          id={`${uid}-input`}
          role="combobox"
          aria-expanded={open}
          aria-controls={`${uid}-list`}
          aria-autocomplete="list"
          aria-activedescendant={open && filtered[active] ? `${uid}-list-${active}` : undefined}
          autoComplete="off"
          className="field pr-10"
          placeholder={placeholder}
          value={open ? query : (selected?.label ?? "")}
          onFocus={openList}
          onClick={openList}
          onChange={(e) => {
            setQuery(e.target.value);
            setActive(0);
            setOpen(true);
          }}
          onKeyDown={onKey}
        />
        <ChevronDown
          size={18}
          aria-hidden
          className={`pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-grey-400 transition-transform duration-[var(--dur-base)] ${open ? "rotate-180" : ""}`}
        />
      </div>
      {open && (
        <div className={popover}>
          <Listbox
            id={`${uid}-list`}
            listRef={listRef}
            options={filtered}
            active={active}
            isSelected={(o) => o.value === value}
            onPick={pick}
            onHover={setActive}
          />
        </div>
      )}
    </div>
  );
}
