"use client";

import { useRouter } from "next/navigation";
import { useApp } from "../shell/app-shell";
import { Setup } from "./setup";

/* / (the home page) */
export default function SetupScreen() {
  const { config, job, setJob } = useApp();
  const router = useRouter();
  return (
    <>
      <h1 className="mb-8 text-4xl">SEO Report Generator</h1>
      <Setup
        config={config}
        hasReport={!!job}
        onBack={() => router.push("/report")}
        onStart={(j) => {
          setJob(j);
          router.push("/report");
        }}
      />
    </>
  );
}
