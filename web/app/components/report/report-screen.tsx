"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useApp } from "../shell/app-shell";
import { Run } from "./run";

/* /report: generation progress, then review and download. */
export default function ReportScreen() {
  const { job, setJob } = useApp();
  const router = useRouter();

  if (!job)
    return (
      <section className="card mx-auto max-w-lg space-y-4 p-10 text-center">
        <h2 className="text-2xl">No report yet</h2>
        <p className="text-grey-600">Pick the period and clients first, then generate the previews.</p>
        <Link href="/" className="btn btn-primary !text-white !no-underline">Go to setup</Link>
      </section>
    );

  return (
    <Run
      key={job.id}
      job={job}
      onJob={setJob}
      onBack={() => router.push("/")}
      onReset={() => {
        setJob(null);
        router.push("/");
      }}
    />
  );
}
