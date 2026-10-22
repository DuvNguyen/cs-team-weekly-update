import io, re
from googleapiclient.http import MediaIoBaseUpload
import voice

MODEL = "gemini-3.1-flash-lite"
URL_RE = re.compile(r"https?://[^\s]+")

def doc_url(doc_id: str) -> str:
    return f"https://docs.google.com/document/d/{doc_id}/edit"

def compose_body(summary: str, this_week: str, next_week: str,
                 category: str = "", trend: str = "", trend_sources: list = None, notes: bool = True) -> str:
    """AI summary paragraph, then the SEO team's raw notes (verbatim, including any Docs/blog
    links) so the PM can click through and adjust, then a short current industry-trend note."""
    parts = [summary]
    if notes and (this_week or next_week):
        parts.append("\nSEO team notes:")
        if this_week:
            parts.append(f"Current 2 weeks: {this_week}")
        if next_week:
            parts.append(f"Next 2 weeks: {next_week}")
    if trend:
        label = f"Industry trend — {category}:" if category else "Industry trend:"
        parts.append(f"\n{label} {trend}")
        for url in (trend_sources or []):
            parts.append(f"Source: {url}")
    return "\n".join(parts)

def build_prompt(name: str, category: str, series: dict, prev: dict, this_week: str, next_week: str) -> str:
    structure = voice.STRUCTURE
    t, p = series["totals"], prev["totals"]
    lines = [
        voice.VOICE,
        voice.EXAMPLES,
        f'Now write the bi-weekly update for the client "{name}".',
        ("Write the email body in these sections, in this order. The greeting and sign-off are added separately, so leave them out. "
         'Return JSON only: {"sections": [{"title": ..., "content": ...}]} with one entry per section, in the same order. '
         '"title" is the section title exactly as given ("" when it has no title); "content" is that section\'s text. '
         "Plain text only inside content, no markdown symbols (no #, no **); start each list item with '- ' on its own line. "
         "This layout overrides any style rule against headings or lists.\n" + structure)
        if structure else "ONE paragraph, 4-6 sentences, in the style above.",
        "",
        f"These 2 weeks (last 14 days): {t['clicks']:,} clicks, {t['impressions']:,} impressions, "
        f"click-through rate {t['ctr']}, average position {t['position']}.",
        f"Previous 2 weeks: {p['clicks']:,} clicks, {p['impressions']:,} impressions, "
        f"click-through rate {p['ctr']}, average position {p['position']}.",
        "Describe the trend versus the previous 2 weeks in clicks and impressions (up or down), "
        "and whether average position improved or worsened (a lower position is better).",
    ]
    if category:
        lines.append(
            f"This client is in: {category}. Where it reads naturally, relate the trend to that "
            "market — but do not invent specific facts or numbers."
        )
    if this_week or next_week:
        lines.append("")
        if this_week:
            lines.append(f"What the SEO team did in the last 2 weeks:\n{this_week}")
        if next_week:
            lines.append(f"Plan for the next 2 weeks:\n{next_week}")
        lines += [
            "",
            "Use the notes for the work and plan sections. Do not invent numbers, tasks, causes or Google updates. "
            "Keep any URL from the notes right after the item it belongs to."
            if structure else
            "Weave in the work done in these 2 weeks, then end with one sentence on what's planned for the next 2 weeks. "
            "Ignore any URLs in the notes. Do not invent numbers or tasks.",
        ]
    else:
        lines += [
            "",
            "There are no task notes for this client this period, so cover the search performance only. "
            "Do not mention that notes or updates are missing, and do not invent any work.",
        ]
    return "\n".join(lines)

def summarize(gemini, name: str, category: str, series: dict, prev: dict, this_week: str, next_week: str) -> str:
    prompt = build_prompt(name, category, series, prev, this_week, next_week)
    resp = gemini.models.generate_content(model=MODEL, contents=prompt)
    return (resp.text or "").strip()

def create_doc(docs, drive, title: str, folder_id: str) -> str:
    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    # move it into the target Drive folder
    drive.files().update(fileId=doc_id, addParents=folder_id, removeParents="root", fields="id, parents").execute()
    return doc_id

def _upload_png(drive, png_path: str, folder_id: str) -> str:
    with open(png_path, "rb") as f:
        media = MediaIoBaseUpload(io.BytesIO(f.read()), mimetype="image/png")
    meta = {"name": png_path.split("/")[-1], "parents": [folder_id]}
    file = drive.files().create(body=meta, media_body=media, fields="id").execute()
    # make it fetchable by the Docs image inserter
    drive.permissions().create(fileId=file["id"], body={"type": "anyone", "role": "reader"}).execute()
    return f"https://drive.google.com/uc?export=view&id={file['id']}"

def append_client(docs, drive, doc_id: str, name: str, png_path: str, summary: str, folder_id: str,
                  category: str = "") -> None:
    img_url = _upload_png(drive, png_path, folder_id)
    # end index of the doc body
    doc = docs.documents().get(documentId=doc_id).execute()
    end = doc["body"]["content"][-1]["endIndex"] - 1
    heading = f"{name}\n" + (f"{category}\n" if category else "")
    requests = [
        {"insertText": {"location": {"index": end}, "text": heading}},
        {"insertInlineImage": {"location": {"index": end + len(heading)},
                               "uri": img_url, "objectSize": {
                                   "width": {"magnitude": 460, "unit": "PT"},
                                   "height": {"magnitude": 200, "unit": "PT"}}}},
    ]
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    # append the summary after the image (re-read end index), and make any URLs clickable
    doc = docs.documents().get(documentId=doc_id).execute()
    end = doc["body"]["content"][-1]["endIndex"] - 1
    text = f"\n{summary}\n\n"
    reqs = [{"insertText": {"location": {"index": end}, "text": text}}]
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,);]")          # drop trailing punctuation from the link
        s = end + m.start()
        reqs.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": s + len(url)},
            "textStyle": {"link": {"url": url}},
            "fields": "link"}})
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()
