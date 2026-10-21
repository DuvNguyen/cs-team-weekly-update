"use client";

import { LogOut, MessageSquareText, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { Job, Me } from "../../lib/api";
import { isWorking } from "../../lib/job";
import { Stepper } from "../report/stepper";

/* One line: wordmark on the left; steps, Voice rules and the account on the right. */
/* Avatar button with a dropdown: who is signed in, Settings, Sign out. */
function AccountMenu({ me, onVoice, onSettings, onSignOut }: { me: Me; onVoice: boolean; onSettings: () => void; onSignOut: () => void }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", away);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", away);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  const item = "flex w-full items-center gap-2 rounded-[var(--radius-md)] px-3 py-2 text-left text-sm font-semibold text-ink hover:bg-grey-100";
  return (
    <div ref={box} className="relative">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-haspopup="menu" aria-expanded={open} aria-label="Account menu" className="flex items-center gap-3 rounded-full text-sm font-semibold text-white">
        <span className="hidden max-w-48 truncate sm:inline">{me.name || me.email}</span>
        <span className="flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-full border border-white/25 bg-white/10 hover:bg-white/20">
          {me.picture ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={me.picture} alt="" referrerPolicy="no-referrer" className="size-full object-cover" />
          ) : (
            (me.name || me.email).charAt(0).toUpperCase()
          )}
        </span>
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-full z-20 mt-2 w-64 rounded-[var(--radius-lg)] bg-white p-2 shadow-lg">
          <p className="truncate px-3 py-2 text-sm text-grey-600">{me.email}</p>
          <Link role="menuitem" href="/voice" aria-current={onVoice ? "page" : undefined} className={`${item} !no-underline ${onVoice ? "bg-brand-050" : ""}`} onClick={() => setOpen(false)}>
            <MessageSquareText size={14} />
            Voice rules
          </Link>
          <button role="menuitem" type="button" className={item} onClick={() => (setOpen(false), onSettings())}>
            <Settings size={14} />
            Settings
          </button>
          {!me.demo && (
            <button role="menuitem" type="button" className={item} onClick={onSignOut}>
              <LogOut size={14} />
              Sign out
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export function Header({ me, signedOut, job, onSignOut, onSettings }: { me: Me | null; signedOut: boolean; job: Job | null; onSignOut: () => void; onSettings: () => void }) {
  const path = usePathname();
  const step = path.startsWith("/setup") ? 1 : path.startsWith("/report") ? (job && isWorking(job) ? 2 : 3) : 0;
  const onVoice = path.startsWith("/voice");

  return (
    <header className="bg-navy">
      <div className="mx-auto grid w-full max-w-[var(--container-max)] grid-cols-[1fr_auto_1fr] items-center gap-6 px-8 py-5">
        {/* Official wordmark, never redrawn */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/wordmark-white.svg" alt="Saigon Digital" className="h-6 w-auto shrink-0" />
        {!signedOut && (
          <>
            <Stepper step={step} hasReport={!!job} />
            <div className="flex justify-end">
              {me && <AccountMenu me={me} onVoice={onVoice} onSettings={onSettings} onSignOut={onSignOut} />}
            </div>
          </>
        )}
      </div>
    </header>
  );
}
