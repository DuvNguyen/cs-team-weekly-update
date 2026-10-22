# email_parts.py — a client's email as parts you can review one by one: greeting, each section, notes / trend, sign-off.
# Each part has an id, kind, title, text, status (review / confirmed / deleted) and whether the person edited it.
# provenance.check_part() says where a part's content comes from and what could not be traced.
import json
import re
import secrets

import provenance

STATUSES = ("review", "confirmed", "deleted")
MAX_TEXT, MAX_TITLE = 20000, 200


def from_generation(raw: str, structured: bool) -> list[dict]:
    """The sections Gemini wrote: [{"title", "text"}]. A style with sections asks for JSON; anything unreadable becomes one section."""
    raw = (raw or "").strip()
    if structured:
        block = re.search(r"\{.*\}", raw, re.S)
        try:
            items = json.loads(block.group(0))["sections"] if block else []
        except (ValueError, KeyError, TypeError):
            items = []
        found = [{"title": " ".join(str(i.get("title", "")).split()), "text": str(i.get("content", "")).strip()}
                 for i in items if isinstance(i, dict) and str(i.get("content", "")).strip()]
        if found:
            return found
    return [{"title": "", "text": raw}]


def _part(kind: str, title: str, text: str, status: str = "review", optional: bool = False) -> dict:
    """optional: left out of the email unless confirmed, and never blocks the client from being ready."""
    return {"id": secrets.token_hex(4), "kind": kind, "title": title, "text": text, "status": status, "edited": False, "optional": optional}


def build(greeting: str, sections: list[dict], ctx: dict, structured: bool, trend: str, sources: list[str], category: str, sender: str) -> list[dict]:
    parts = [_part("greeting", "", greeting, "confirmed")]
    parts += [_part("section", s["title"], s["text"]) for s in sections]
    notes = [f"Current 2 weeks: {ctx['this_week']}" if ctx.get("this_week") else "", f"Next 2 weeks: {ctx['next_week']}" if ctx.get("next_week") else ""]
    if not structured and any(notes):                    # a style with sections already covers the work in its sections
        parts.append(_part("notes", "SEO team notes", "\n".join(n for n in notes if n)))
    if ctx.get("trends"):                                # the SEO sheet's Trends/News cell: always offered for review, whatever the style
        parts.append(_part("trends", "SEO trends / news", ctx["trends"], optional=True))
    if trend:
        parts.append(_part("trend", f"Industry trend — {category}" if category else "Industry trend", "\n".join([trend] + [f"Source: {u}" for u in sources])))
    parts.append(_part("signoff", "", f"Best regards,\n{sender}\nSaigon Digital", "confirmed"))
    return parts


def compose_body(parts: list[dict]) -> str:
    """The email as text, without the deleted parts (the same layout the single text box used to hold)."""
    kept = [p for p in parts if p["status"] != "deleted" and (not p.get("optional") or p["status"] == "confirmed")]
    return "\n\n".join((f"{p['title']}\n{p['text']}" if p["title"] else p["text"]) for p in kept if p["text"] or p["title"])


def _find(parts: list[dict], part_id: str) -> dict:
    part = next((p for p in parts if p["id"] == part_id), None)
    if part is None:
        raise ValueError("That part of the email no longer exists.")
    return part


def update_part(parts: list[dict], part_id: str, patch: dict, ctx: dict) -> dict:
    """Edit, confirm, delete or restore one part. Editing makes it need a new confirmation."""
    part = _find(parts, part_id)
    status = patch.get("status")
    if status is not None and status not in STATUSES:
        raise ValueError(f"Unknown status “{status}”.")
    for field, limit in (("text", MAX_TEXT), ("title", MAX_TITLE)):
        if field in patch:
            value = str(patch[field])
            if len(value) > limit:
                raise ValueError(f"The {field} is too long (max {limit} characters).")
            if value != part[field]:
                part[field], part["edited"], part["status"] = value, True, "review"
    if status == "confirmed":
        flags = provenance.check_part(part, ctx)["flags"]
        if flags and not part["edited"]:
            raise ValueError(f"This part has details that are not in the sources. {flags[0]} Edit it, or delete it.")
    if status is not None:
        part["status"] = status
    return part


def confirm_all(parts: list[dict], ctx: dict) -> tuple[list[str], list[str]]:
    """Confirm every part still in review that has nothing flagged (or that the person already edited).
    Flagged parts are left for the person: (ids confirmed, ids that still need checking)."""
    done, skipped = [], []
    for part in parts:
        if part["status"] != "review":
            continue
        if provenance.check_part(part, ctx)["flags"] and not part["edited"]:
            skipped.append(part["id"])
        else:
            part["status"] = "confirmed"
            done.append(part["id"])
    return done, skipped


def reviewed_count(parts: list[dict]) -> tuple[int, int]:
    """(reviewed, total) over the parts that must be reviewed; optional parts are not counted."""
    required = [p for p in parts if not p.get("optional")]
    return sum(p["status"] != "review" for p in required), len(required)


def ready(parts: list[dict]) -> bool:
    """Every part confirmed or deleted, and something left to send."""
    required = [p for p in parts if not p.get("optional")]
    return bool(parts) and all(p["status"] != "review" for p in required) and any(p["status"] == "confirmed" for p in required)
