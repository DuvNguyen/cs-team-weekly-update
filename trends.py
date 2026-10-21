# trends.py — one short, current industry-trend note per client category.
# Uses Gemini with Google Search grounding so the note reflects the real web, not model memory.
from google.genai import types

PROMPT = (
    "Search the web for what is happening RIGHT NOW in SEO and online search behaviour for "
    "businesses in this industry: {category}.\n"
    "Write 2-3 sentences, plain English, for a business owner (not an SEO expert):\n"
    "- one current trend or shift in how their customers search, and\n"
    "- one concrete thing that could improve their search performance because of it.\n"
    "Only state trends you actually found in the search results. Be specific, no filler, "
    "no bullet points, no headings. Do not invent statistics."
)

def for_category(gemini, category: str, model: str):
    """Return (text, [source_urls]). Returns ('', []) if the lookup fails — the report
    must still build without a trend note."""
    try:
        resp = gemini.models.generate_content(
            model=model,
            contents=PROMPT.format(category=category),
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]),
        )
        text = (resp.text or "").strip()
        sources = []
        try:                                    # grounding metadata is best-effort
            for chunk in resp.candidates[0].grounding_metadata.grounding_chunks[:2]:
                sources.append(chunk.web.uri)
        except Exception:
            pass
        return text, sources
    except Exception:
        return "", []
