import type { Job } from "./api";

const BUSY = ["queued", "signing_in", "running"];

/** True while the backend is still generating, or any client is still pending or running. */
export const isWorking = (j: Job) =>
  BUSY.includes(j.status) || j.clients.some((c) => c.status === "running" || c.status === "pending");
