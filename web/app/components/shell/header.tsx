"use client";

import { LogOut, MessageSquareText } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Job, Me } from "../../lib/api";
import { isWorking } from "../../lib/job";
import { Stepper } from "../report/stepper";

/* One line: wordmark on the left; steps, Voice rules and the account on the right. */
export function Header({ me, signedOut, job, onSignOut }: { me: Me | null; signedOut: boolean; job: Job | null; onSignOut: () => void }) {
  const path = usePathname();
  const step = path.startsWith("/setup") ? 1 : path.startsWith("/report") ? (job && isWorking(job) ? 2 : 3) : 0;
  const onVoice = path.startsWith("/voice");

  return (
    <header className="bg-navy">
      <div className="mx-auto flex w-full max-w-[var(--container-max)] items-center justify-between gap-6 px-8 py-5">
        {/* Official wordmark, never redrawn */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/wordmark-white.svg" alt="Saigon Digital" className="h-6 w-auto shrink-0" />
        {!signedOut && (
          <div className="flex items-center gap-4">
            <Stepper step={step} hasReport={!!job} />
            <Link
              href="/voice"
              aria-current={onVoice ? "page" : undefined}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-semibold !no-underline transition-colors duration-[var(--dur-fast)] ${
                onVoice ? "border-white bg-white !text-indigo" : "border-white/25 !text-white hover:bg-white/10"
              }`}
            >
              <MessageSquareText size={14} />
              Voice rules
            </Link>
            {me && !me.demo && (
              <div className="flex items-center gap-3 text-sm text-white/80">
                <span className="hidden xl:inline">{me.email}</span>
                <button type="button" onClick={onSignOut} className="inline-flex items-center gap-1.5 rounded-full border border-white/25 px-3.5 py-1.5 font-semibold text-white hover:bg-white/10">
                  <LogOut size={14} />
                  Sign out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
