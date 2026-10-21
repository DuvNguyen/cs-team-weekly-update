"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ApiError, type Config, type Job, type Me } from "../../lib/api";
import { Login } from "../report/login";
import { Alert, Skeleton } from "../ui/feedback";
import { Header } from "./header";

/* What every page can read: who is signed in, the config, and the report job being worked on. */
type App = { me: Me; config: Config; job: Job | null; setJob: (j: Job | null) => void };
const AppContext = createContext<App | null>(null);

export function useApp(): App {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppShell");
  return ctx;
}

/* Header, sign-in gate and shared state. Layouts persist across navigation, so the job survives page changes. */
export function AppShell({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [needLogin, setNeedLogin] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [authError] = useState(() =>
    typeof window === "undefined" ? "" : (new URLSearchParams(window.location.search).get("auth_error") ?? ""),
  );

  // Who am I? 401 means no session: show the login screen. Otherwise load the config.
  useEffect(() => {
    api
      .me()
      .then((m) => {
        setMe(m);
        return api.config().then(setConfig);
      })
      .catch((e) => (e instanceof ApiError && e.status === 401 ? setNeedLogin(true) : setLoadError(e.message)));
  }, []);

  async function signOut() {
    await api.logout().catch(() => {});
    window.location.reload();
  }

  return (
    <>
      <Header me={me} signedOut={needLogin} job={job} onSignOut={signOut} />
      <main className="mx-auto w-full max-w-[var(--container-max)] flex-1 px-8 py-10">
        {needLogin ? (
          <Login reason={authError} />
        ) : loadError ? (
          <Alert>Could not reach the backend ({loadError}). Is the Python server running on port 8000?</Alert>
        ) : !me || !config ? (
          <div className="grid gap-8 lg:grid-cols-12">
            <Skeleton className="h-56 lg:col-span-5" />
            <Skeleton className="h-72 lg:col-span-7" />
          </div>
        ) : (
          <AppContext.Provider value={{ me, config, job, setJob }}>{children}</AppContext.Provider>
        )}
      </main>
    </>
  );
}
