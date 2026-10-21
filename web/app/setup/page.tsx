import { redirect } from "next/navigation";

// Setup moved to the home page; this keeps old bookmarks working.
export const instant = false;

export default function SetupPage() {
  redirect("/");
}
