import { redirect } from "next/navigation";

// Rendered behind the client-side sign-in gate (AppShell), so there is nothing to pre-validate.
export const instant = false;

export default function Home() {
  redirect("/setup");
}
