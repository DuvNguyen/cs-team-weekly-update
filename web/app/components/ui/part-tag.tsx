import type { PartTag as Tag } from "../../lib/api";
import { Badge } from "./feedback";

const TAGS: Record<Tag, { tone: "neutral" | "sky" | "green" | "amber" | "blue"; label: string; hint: string }> = {
  template: { tone: "neutral", label: "Template", hint: "Standard greeting or sign-off" },
  gsc: { tone: "sky", label: "Search Console", hint: "Its numbers match the Search Console data" },
  notes: { tone: "green", label: "SEO team notes", hint: "Taken from the SEO team's notes in the sheet" },
  ai: { tone: "amber", label: "AI wording", hint: "Sentences written by Gemini" },
  trend: { tone: "neutral", label: "Google Search via Gemini", hint: "Industry trend found by Gemini with Google Search" },
  you: { tone: "blue", label: "Edited by you", hint: "You changed this part" },
};

/* Where a part of an email comes from. The check behind it runs in code, not on the AI's say-so. */
export function PartTag({ tag }: { tag: Tag }) {
  const t = TAGS[tag];
  return (
    <span title={t.hint}>
      <Badge tone={t.tone}>{t.label}</Badge>
    </span>
  );
}
