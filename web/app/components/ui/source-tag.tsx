import type { Source } from "../../lib/api";
import { Badge } from "./feedback";

/* Where a heading or a note came from: the pasted email (trusted), an AI draft (not yet confirmed), or the user. */
export function SourceTag({ source }: { source?: Source }) {
  if (source === "email") return <Badge tone="sky">From the email</Badge>;
  if (source === "ai") return <Badge tone="amber">AI draft</Badge>;
  if (source === "you") return <Badge tone="blue">Edited by you</Badge>;
  return null;
}
