# provenance.py — where does each part of a client email come from? Checked by code, never by the AI's say-so.
#   Search Console: every number is compared with the real totals (and their changes) and with the SEO team's notes.
#   SEO team notes: a bullet line counts only if its words (or its link) really appear in the sheet notes.
#   Anything else is "ai" wording. A number or bullet that traces to neither is flagged for the person to check.
import re

URL_RE = re.compile(r"https?://\S+")
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
DATE_RE = re.compile(rf"\b{_MONTH}\s+\d{{1,2}}\b|\b\d{{1,2}}\s+{_MONTH}", re.I)
LIST_NO_RE = re.compile(r"^\s*\d+[.)]\s+", re.M)
NUM_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
BULLET_RE = re.compile(r"^\s*[-•*]\s+")
ALWAYS_OK = {2.0, 14.0}                         # "these 2 weeks (last 14 days)" is how the period is worded everywhere
STOP = set("""the and for with from into over per our you your their this that these those are was were been has have had not but
              one two three four five six seven eight nine ten new more also its out all any can will""".split())
OVERLAP = 0.6                                    # share of a bullet's words that must appear in the notes ...
COVERS = 0.75                                    # ... or the share of one notes line a bullet must cover (extra wording is fine)


def _strip(text: str) -> str:
    return LIST_NO_RE.sub("", DATE_RE.sub(" ", URL_RE.sub(" ", text or "")))


def numbers_in(text: str) -> list[str]:
    return NUM_RE.findall(_strip(text))


def _value(token: str) -> tuple[float, int]:
    plain = token.rstrip("%").replace(",", "")
    return float(plain), (len(plain.split(".")[1]) if "." in plain else 0)


def _float(v) -> float | None:
    try:
        return float(str(v).rstrip("%").replace(",", ""))
    except ValueError:
        return None


def allowed_numbers(ctx: dict) -> list[float]:
    """Every number a client email may quote: the totals of both periods, their change and % change, and any number in the notes."""
    allowed = set(ALWAYS_OK)
    now, prev = (ctx.get("series") or {}).get("totals") or {}, (ctx.get("prev") or {}).get("totals") or {}
    for key in ("clicks", "impressions", "ctr", "position"):
        a, b = _float(now.get(key)), _float(prev.get(key))
        for v in (a, b):
            if v is not None:
                allowed.add(v)
        if a is not None and b is not None:
            allowed.add(abs(a - b))
            if b:
                allowed.add(abs(a - b) / b * 100)
    notes = f"{ctx.get('this_week', '')}\n{ctx.get('next_week', '')}"
    allowed.update(_value(t)[0] for t in numbers_in(notes))
    return sorted(allowed)


def _stem(word: str) -> str:
    """Crude on purpose: published/publish, titles/title, pages/page, fixed/fix all meet at the same short stem."""
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            break
    if word.endswith("e") and len(word) > 3:
        word = word[:-1]
    return word[:5]


def _words(text: str) -> list[str]:
    return [_stem(w) for w in re.findall(r"[a-z]+", URL_RE.sub(" ", text).lower()) if len(w) >= 3 and w not in STOP]


def traces_to_notes(line: str, notes: str) -> bool:
    """A bullet is supported when a link in it is in the notes, or most of its words are."""
    urls = [u.rstrip(".,);]") for u in URL_RE.findall(line)]
    if any(u in notes for u in urls):
        return True
    words, known = _words(line), set(_words(notes))
    if not words or sum(w in known for w in words) / len(words) >= OVERLAP:
        return True
    mine = set(words)
    for note in filter(str.strip, notes.splitlines()):
        theirs = set(_words(note))
        if len(theirs) >= 2 and len(theirs & mine) / len(theirs) >= COVERS:
            return True
    return False


def check_part(part: dict, ctx: dict) -> dict:
    """{"tags": [...], "numbers": {"matched", "unmatched"}, "lines": [{"text", "tag"}], "flags": [...]} for one part of an email."""
    kind, text = part.get("kind"), part.get("text") or ""
    out = {"tags": [], "numbers": {"matched": [], "unmatched": []}, "lines": [], "flags": []}
    if kind in ("greeting", "signoff"):
        out["tags"] = ["template"]
    elif kind == "notes":
        out["tags"] = ["notes"]
    elif kind == "trend":
        out["tags"] = ["trend"]
    elif kind == "trends":                      # the SEO sheet's "Trends/News" cell, shown as written
        out["tags"] = ["sheet"]
    else:
        allowed, notes = allowed_numbers(ctx), f"{ctx.get('this_week', '')}\n{ctx.get('next_week', '')}"
        for token in numbers_in(text):
            value, decimals = _value(token)
            ok = any(round(a, decimals) == value for a in allowed)
            out["numbers"]["matched" if ok else "unmatched"].append(token)
        out["flags"] += [f"{t} is not in the Search Console data or the SEO team's notes." for t in out["numbers"]["unmatched"]]
        prose = False
        for raw in filter(str.strip, text.splitlines()):
            if BULLET_RE.match(raw):
                line = BULLET_RE.sub("", raw).strip()
                traced = traces_to_notes(line, notes)
                out["lines"].append({"text": raw.strip(), "tag": "notes" if traced else "flag"})
                if not traced:
                    out["flags"].append(f"Not found in the SEO team's notes: {line}")
            else:
                prose = True
        used = {l["tag"] for l in out["lines"]}
        out["tags"] = (["gsc"] if out["numbers"]["matched"] else []) + (["notes"] if "notes" in used else []) + (["ai"] if prose else [])
    if part.get("edited"):
        out["tags"].append("you")
    return out
