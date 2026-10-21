# CS Tools Plan (Rock Q4 2026)

Status: **planning**, CS team requests expected later today. This file is the working plan; update it as requests land.

Scope: the Client Success (CS) side of the Rock.

| # | Tool | Rock goal | Due |
|---|------|-----------|-----|
| A | Weekly SEO Update UI (wrap the existing Python tool) | Goal 2 | Nov 20 |
| B | Account Manager Report builder (new, this doc) | new ask | TBD with CS |
| C | SD Friday to Google Slides exporter | Goal 3 | Dec 4 |

A and B should share one web app, one login and one UI shell. C joins later as a third module.

---

## 1. Tool A: Weekly SEO Update UI

### What exists today
`run.py` builds one Google Doc for 13 clients: GSC data (current vs previous 14 days) per client, a chart, a Gemini-written paragraph in house style, and the SEO team's notes from a Google Sheet tab. Run via `weekly-report.command` on macOS. Setup needs hand-editing `config.json`.

### Gaps to close
- No UI. The tab name and client list are edited as JSON.
- macOS and Terminal only.
- No preview: the Doc is created straight away.
- No retry for a single failed client.
- Secrets (Gemini key, OAuth client) sit in the shared folder.

### Decided
- **Preview before the Doc is created.** CS reviews and edits each client's chart and paragraph, then confirms. The Google Doc is only created on confirm.

### Flow
1. Pick period (default: last 14 days ending 2 days ago) and SEO sheet tab (dropdown read from the sheet).
2. Tick clients (list is managed in a settings page).
3. Generate: per-client progress and status. A failed client shows its error and a Retry button.
4. Preview: one card per client with chart, editable paragraph, editable notes, Regenerate paragraph.
5. Confirm: create the Doc in the Drive folder, then show an Open Doc button.

### Reuse
Keep `gsc.py`, `report.py`, `trends.py`, `voice.py`, `chart.py`, `updates.py`, `dates.py`. Wrap them as a Python service (FastAPI) and split `run.py` into two steps, `generate()` and `publish()`, so the preview can sit between them.

---

## 2. Tool B: Account Manager Report builder

### The problem
Every Friday by 4:00 PM, the Account Manager writes "Account Manager End-of-Week Report & Sync Prep" by hand in Word. The reviewer is the COO (Jonas). Source sample: `docs/15 (16.10) - Account Manager Report & Sync Prep.docx`.

The structure is the same each week. Only the answers change. Retyping the questions, pasting screenshots and re-formatting is the waste.

### Document structure (from the sample)
**Header**: Title, Submitted by, Date of Submission (due every Friday 4:00 PM), Reviewer.

**1. Department-Specific Operations**
- **A. Development**: three prompts, each with a free-text answer: Developer Task Lock-In (with screenshots/links of the project board), Scope Creep & Upsell Tracking, Cross-Department Handovers.
- **B. Account Management (AM) Sync**: Client Deliverable Alignment, with two bullet lists, *Last week* and *This week*, each item being `Client: status`. Then Blocker Resolution (free text) and Weekly Updates Added to SD Friday (yes/no plus note).
- **C. SEO Department**: Lead Alignment (with screenshots), Task Delegation Audit, Tooling & Technical Support.

**2. Monday Townhall & Operations Prep**: Townhall Presentation Ready (with link), Meeting Logistics & Links, Weekly WFH/In-Office Roster.

**Footer**: signature table (Account Manager name/date, COO name/date).

### Approach: "CV builder" style
A form on the left, a live document preview on the right, and an **Export** button.

- **Fixed prompts** live in a template definition (JSON). They are not retyped each week.
- **Answers** are inputs matched to the prompt type: short text, rich text, bullet list, image upload or paste, link, yes/no plus note.
- **Client status list** is a repeatable row (client dropdown + status text) with add, remove and reorder. Clients come from the same client list as Tool A.
- **Carry over from last week.** The previous report's *This week* becomes the new report's *Last week*. This is the biggest time saver.
- **Autosave drafts** per week, so nothing is lost and the report can be finished across the day.
- **Export** to `.docx` matching the current layout. Optionally also export to a Google Doc.
- **Defaults:** submitter, reviewer and the due date (next Friday) pre-filled.

### Implementation notes
- Generate the `.docx` by filling a template file derived from the sample (docxtpl, or python-docx) so the look matches what Jonas already gets. Pasted images go in as inline pictures.
- Store the template schema as data. A new or changed question is then a config change, not a code change.
- Later option: pre-fill the *Last week* / *This week* client bullets from SD Friday (shared with Tool C).

---

## 3. Shared architecture

- **Frontend:** Next.js (React), one app with modules: Weekly Report, AM Report, later Slides Export.
- **Backend:** FastAPI wrapping the existing Python logic. Next.js route handlers can proxy to it.
- **Storage:** a small database (SQLite or Postgres) for drafts, client list, report history and settings.
- **Auth:** Google sign-in for CS users. GSC, Sheets, Docs and Drive calls run either as each user or through one service account (see open questions).
- **Secrets:** env vars only. Nothing in `config.json` or a shared folder.
- **Hosting:** one internal URL, so there is nothing to install and no macOS permission issues.

---

## 4. Open questions

Ask CS when their requests arrive.

1. **Weekly, bi-weekly, or both?** The tool says bi-weekly; the Rock doc says weekly/bi-weekly. This decides the period picker and defaults.
2. **Can CS add and remove clients themselves?** Assumed yes (settings page, since adding clients is common). Confirm.
3. **Web app vs desktop.** Web is the recommendation. Confirm no one needs offline.
4. **Google access model:** each CS user signs in with their own account, or one shared account (developers@) as today?
5. **AM Report:** who fills it, one person or several? Is Google Doc output acceptable, or must it be `.docx`?
6. **AM Report:** should the client bullets auto-pull from SD Friday, or stay manual?
7. **AM Report:** do CS want history/search of past reports, and does the COO need a review/approve step in the app?
8. **AM Report:** any sections that change (new departments, new questions)? Are the prompts editable by CS or only by us?

## 5. Risks and notes

- The Gemini API key and OAuth client secret in `/projects/weekly-update-tool` should be rotated and moved to env vars.
- Google API quotas: 13+ clients per run is fine, but add retry with backoff.
- Match the docx layout carefully. Jonas reviews the output, so visual drift will get noticed.

## 6. Build order

1. **Tool A, MVP:** split `run.py` into generate/publish, add the API, then the UI with client picker, tab dropdown, progress, preview and publish. Done when a non-tech CS user produces a report without Terminal.
2. **Tool B, MVP:** template schema, form, live preview, `.docx` export, carry-over from last week, autosave.
3. **Polish:** settings page, per-client retry, history, user guide/SOPs (due Nov 20).
4. **Tool C** after A and B (due Dec 4).
5. Fold in CS requests as they arrive today and re-prioritise this list.
