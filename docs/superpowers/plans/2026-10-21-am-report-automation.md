# Account Manager Report Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A page in the Weekly Update app that reads SD Friday (read-only), builds the "Account Manager Report & Sync Prep" `.docx` (same sections, wording and bullets as the sample, a cleaner Saigon Digital look), and downloads it, leaving everything SD Friday can't supply blank and highlighted.

**Architecture:** Flat Python modules next to the existing ones: a read-only Postgres client (`sdf.py`), pure workload maths (`workload.py`), a row-image renderer (`workload_pic.py`), a bullet builder (`am_bullets.py`), a template filler (`am_docx.py`), a small settings store (`am_settings.py`) and a FastAPI router (`am_web.py`, same pattern as `settings_web.py`). A new Next.js page `/am-report` reached from the account dropdown.

**Tech Stack:** Python 3.12 + FastAPI, psycopg 3, python-docx, matplotlib (all already in `.venv`; add `psycopg[binary]` to `requirements.txt`), Next.js 16 / React 19, pytest.

**Spec:** `docs/superpowers/specs/2026-10-21-am-report-automation-design.md`. The workload maths must match SD Friday's own code: `/home/levi/Desktop/Projects/digital-timesheet/app/api/workload/tasks/route.ts` and `components/workload/WorkloadChart.tsx` (read-only reference, never edit it). The sample `docs/15 (16.10) - Account Manager Report & Sync Prep.docx` is the reference for wording and order.

## Global Constraints

- Read-only: only fixed `select` statements, no user text in SQL. Connection string is `SDF_READONLY_DB_URL` in `.env` (gitignored); the `wut_readonly` role can read `tasks`, `projects(id, name)` and `profiles(id, full_name, sheet_name, department, role, expected_hours, is_active)` only.
- The connection string, passwords and people's emails are never logged, printed, returned by the API or sent to the browser. Names come from `full_name` (fall back to `sheet_name`).
- The sample in `docs/` is never modified; output goes to `out/` (gitignored). The report keeps the sample's sections, wording, order and bullets; only the appearance changes.
- Never keep the sample's answers ("None", "Yes", "Nein.", the CRCC note, dated bullets): clear them, fill from data or leave a yellow-highlighted empty line.
- Blank means blank: no invented text.
- Weeks are Monday to Friday. Port stays 3000. No Gemini in this version.
- Follow existing style: short module comments, no docstring essays, tests in `tests/test_<module>.py`.

## Review Focus

- `SDF_READONLY_DB_URL` missing or wrong: clear message, 503, nothing written. (Task 1, Task 6)
- A roster name that matches nobody in `profiles`: shown as a warning, its row is skipped, the report still builds. (Task 5)
- A task with no estimate, no dates, or only weekend dates; a person with `expected_hours` 0 or null: no crash, no division by zero, grey bubble. (Tasks 2, 3)
- Task or project names with odd characters or very long text in the `.docx`. (Task 4)
- A picked date that isn't a Monday, or a week with no tasks at all: normalised to Monday; empty data gives blanks, not an error. (Tasks 2, 5)
- Picture route given `../` or an unknown name: 404, never reads outside `out/`. (Task 6)

---

## File Structure

| File | Responsibility |
|---|---|
| `sdf.py` | Read-only connection and the three fixed queries |
| `workload.py` | Pure maths: per-person daily hours for a week; bubble status |
| `workload_pic.py` | Draws one person-row PNG in the sample's dark style |
| `am_bullets.py` | Status mapping, client bullets, blockers (pure) |
| `am_settings.py` | Submitter, reviewer, rosters; JSON in `data/` |
| `am_template.json` | The sample's headings and prompts, word for word, as data |
| `am_docx.py` | Builds the styled `.docx` from that data and the report values |
| `am_web.py` | Router: settings, generate, pictures, export |
| `web/app/am-report/page.tsx`, `web/app/components/am/am-report.tsx` | The page |

---

### Task 1: Read-only SD Friday client

**Files:** Create `sdf.py`, `tests/test_sdf.py`. Modify `requirements.txt`.

**Interfaces:**
- Produces: `class SdfNotConfigured(Exception)`; `fetch_tasks(start: date, end: date) -> list[dict]`; `fetch_people() -> list[dict]` (keys `id, name, department, role, expected_hours`); `fetch_projects() -> dict[str, str]` (id to name).

- [ ] **Step 1: Failing tests** with a fake connection injected via `sdf._connect` monkeypatch: `test_missing_url_raises_not_configured` (env unset → `SdfNotConfigured`); `test_queries_are_selects_only` (every statement the fake saw starts with `select`); `test_person_name_prefers_full_name_then_sheet_name`; `test_people_never_include_email` (no key `email` in results).
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_sdf.py -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `sdf.py`. `_connect()` reads `SDF_READONLY_DB_URL` via `os.environ` (call `load_dotenv()` like `pipeline.py`), opens `psycopg.connect(url, connect_timeout=10)`, raises `SdfNotConfigured` when unset. `fetch_tasks` selects the columns listed in `app/api/workload/tasks/route.ts` (status, pic_id, peer_reviewer_id, qa_qc_id, publisher_id, project_id, the four `*_estimation`, four `*_time_tracked`, all phase start/due dates, `is_deleted = false`) for tasks overlapping `[start, end]` in any phase, mirroring that route's overlap rule.
- [ ] **Step 4: Run tests** → PASS. Add `psycopg[binary]` to `requirements.txt`.
- [ ] **Step 5: Commit** `feat: read-only SD Friday client`.

### Task 2: Workload maths

**Files:** Create `workload.py`, `tests/test_workload.py`.

**Interfaces:**
- Consumes: task dicts from Task 1 (`fetch_tasks`), people from `fetch_people`.
- Produces: `monday_of(d: date) -> date`; `daily_hours(tasks: list[dict], week_start: date) -> dict[str, dict[date, float]]` (person id to date to hours, Monday to Friday keys only); `bubble_status(hours: float, expected: float) -> str` returning `"none" | "under" | "optimal" | "over"`.

- [ ] **Step 1: Failing tests:** `test_monday_of_wednesday`; `test_task_spreads_evenly_over_weekdays` (10h, Mon–Fri phase → 2h each day); `test_weekend_days_get_nothing`; `test_remaining_hours_subtract_tracked` (estimate 8, tracked 2 → 6 total); `test_active_phase_follows_status` (status "Peer Review" charges the peer reviewer's phase, not the PIC's); `test_task_without_estimate_or_dates_is_skipped`; `test_bubble_status_thresholds` (0 → none, below expected → under, equal → optimal, above → over; expected 0 or None treated as 7).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** by porting `getActiveAssignee`/`getActiveDates`/`getActiveEstimation` and the spread loop from SD Friday's route and `WorkloadChart.tsx` (lines ~260–345 and the status computation). Define "optimal" exactly as that file does; read it rather than guessing, and put a comment with the source path.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: workload maths matching SD Friday`.

### Task 3: Person-row picture

**Files:** Create `workload_pic.py`, `tests/test_workload_pic.py`.

**Interfaces:**
- Consumes: `bubble_status` from Task 2.
- Produces: `render_row(name: str, expected: float, week: dict[date, float], out_path: str) -> str` (writes a PNG, returns the path). `week` has Monday to Friday keys; two grey weekend dots are always drawn.

- [ ] **Step 1: Failing tests:** `test_writes_a_png` (file exists, opens with Pillow-free check: first 8 bytes are the PNG signature); `test_bubble_colours` (render 3 rows with under/optimal/over hours; sample the pixel at each bubble centre and assert blue/green/red within tolerance: `#60a5fa`-like blue, green `#22c55e`, red `#ef4444`); `test_zero_hours_is_grey`; `test_zero_expected_does_not_crash`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** with matplotlib (`Agg`), like `chart.py`. Look: dark navy background, name bold on the left with "{expected:g}h/day expected" under it, five bubbles with the hours text inside (`6.8h`), size growing with `hours / max(expected, 7)` as in `getBubbleSize`, two small grey weekend dots, wide aspect like the sample crops (~800×64 px per row).
- [ ] **Step 4: Run** → PASS. Open one rendered PNG next to the sample crop to eyeball the match (Read the image).
- [ ] **Step 5: Commit** `feat: draw workload row pictures`.

### Task 4: Styled report builder

**Files:** Create `am_template.json`, `am_docx.py`, `tests/test_am_docx.py`.

**Interfaces:**
- Produces: `build(out_path: str, data: dict) -> list[str]` returning the prompts left blank. `data` keys: `submitter`, `reviewer`, `date_text`, `dev_pictures: list[str]`, `seo_pictures: list[str]`, `last_week: list[str]`, `this_week: list[str]`, `blockers: list[str]`; missing or empty means blank. `am_template.json` holds, in order, the title, header labels, section and sub-section headings, each prompt and objective line, and the signature-table labels, copied word for word from the sample (extract them with python-docx; never retype).

- [ ] **Step 1: Failing tests:** `test_every_sample_prompt_is_present_in_order` (each prompt and heading from the sample `.docx` appears in the output, same order, same wording); `test_sample_answers_are_not_copied` (no "Nein.", "CRCC Asia", "Kenno feedback"); `test_header_filled`; `test_bullets_under_last_and_this_week` (real list paragraphs, not typed "-" characters); `test_pictures_sit_under_their_sections` (picture count equals `len(dev)+len(seo)`, dev ones under A, SEO ones under C); `test_unfilled_prompts_are_highlighted_and_returned` (yellow highlight on the empty answer line; returned list contains e.g. `"Scope Creep & Upsell Tracking"`); `test_sample_file_is_unchanged` (hash before and after); `test_odd_and_long_text_is_safe` (`&`, `<`, quotes, emoji, 500 characters).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** with python-docx: a new document, A4, brand look (navy `#031425`-style headings and the project's blue accent from `web/app/styles/colors.css`, a clean sans font that Word has, spacing between prompts, a shaded header block, a tidy signature table at the end). Bullets use Word's built-in "List Bullet" style. Pictures use `add_picture` at the page text width.
- [ ] **Step 4: Run** → PASS. Convert the output to PDF with `soffice --headless` if available (else open it in Word), view a page as an image, and check it looks tidy next to the sample.
- [ ] **Step 5: Commit** `feat: build the styled AM report`.

### Task 5: Settings, bullets, blockers and the data assembly

**Files:** Create `am_settings.py`, `am_bullets.py`, `tests/test_am_settings.py`, `tests/test_am_bullets.py`.

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: `am_settings.load() -> dict` (keys `submitter` default "Nguyen", `reviewer` default "Jonas (COO)", `dev_roster: list[str]` default `["Le Minh Tri", "Vi Nguyen"]`, `seo_roster: list[str]` default `["Thang Dam Quyet", "Nguyen Nguyen Thi My"]`), `am_settings.save(d: dict) -> dict` (validates types and lengths, strips). `am_bullets.status_group(status: str) -> str` (Planned / In Progress / QA / Completed per SD Friday's `docs/account-manager-weekly-updates-spec.md`; unknown statuses are In Progress); `am_bullets.client_bullets(tasks, projects, week_start) -> tuple[list[str], list[str]]` (last week, this week, one `Project: summary` line per project that had tasks; the summary is the counts and top task names by group); `am_bullets.blockers(tasks, projects) -> list[str]` (`Task name (Project): status` for Stuck and On Hold); `am_bullets.match_roster(roster: list[str], people: list[dict]) -> tuple[list[dict], list[str]]` (matched people, unmatched names).

- [ ] **Step 1: Failing tests:** settings round-trip and defaults; `test_status_groups`; `test_bullets_group_by_project`; `test_blockers_only_stuck_and_on_hold`; `test_unmatched_roster_name_is_reported_not_fatal`; `test_empty_week_gives_empty_lists`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.** Settings file at `os.path.join(sessions.DATA_DIR, "am_settings.json")`, same style as `voice_store.py`. Name matching is case-insensitive on `full_name` or `sheet_name`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: AM report settings and bullets`.

### Task 6: API router

**Files:** Create `am_web.py`, `tests/test_am_web.py`. Modify `server.py` (import and `app.include_router(am_web.router)`).

**Interfaces:**
- Produces, all behind `auth_web.require_user`: `GET /api/am-report/settings`; `PUT /api/am-report/settings`; `POST /api/am-report/generate` body `{week: "YYYY-MM-DD"}` returning `{week_start, data, pictures: [{section, person, week, name}], blank: [str], warnings: [str]}`; `GET /api/am-report/pictures/{name}`; `POST /api/am-report/export` body is the (possibly edited) `data` plus `week_start`, returns the `.docx` with `Content-Disposition`.

- [ ] **Step 1: Failing tests** (TestClient, `sdf` functions monkeypatched, `WUT_DEMO=1` so the gate passes; pattern in `tests/test_settings_web.py`): `test_generate_returns_blanks_and_pictures`; `test_not_configured_returns_503_and_writes_nothing`; `test_picture_route_rejects_traversal_and_unknown_names` (`../x`, `..%2Fx`, unknown → 404); `test_export_returns_docx_and_leaves_template_untouched`; `test_non_monday_week_is_normalised`; `test_empty_week_still_builds`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.** Pictures are written to `out/am-report/<week>/` with generated names (`dev-<n>-this.png`); the route serves only names matching `^[a-z0-9-]+\.png$` that exist in that folder. Export builds a fresh file in `out/am-report/` named `Account Manager Report <dd.mm> .docx`.
- [ ] **Step 4: Run** → PASS, then run the whole suite: `.venv/bin/python -m pytest tests -q`.
- [ ] **Step 5: Commit** `feat: AM report API`.

### Task 7: The page

**Files:** Create `web/app/am-report/page.tsx`, `web/app/components/am/am-report.tsx`. Modify `web/app/lib/api.ts` (types and calls), `web/app/components/shell/header.tsx` (menu item "AM report" under Voice rules, with `FileText` icon, active style like Voice rules).

**Interfaces:**
- Consumes: the Task 6 endpoints through `api` in `lib/api.ts` (`amSettings`, `saveAmSettings`, `amGenerate`, `amExport`).

- [ ] **Step 1:** Add the types and calls to `api.ts`, following its `call`/`send` style; `amExport` downloads the file like `downloadDocx`.
- [ ] **Step 2:** Build the page with the existing `Card`, `Alert`, `ExpandableAlert` components: a week picker (default current week), a Settings card (submitter, reviewer, the two rosters as comma-separated lines, Save), a Generate button, then the filled sections as editable text areas with the pictures shown under them and blank ones marked, and a **Download .docx** button. Show warnings (unmatched names) in an `Alert`. Show the 503 message plainly: "SD Friday isn't connected. Add SDF_READONLY_DB_URL to .env."
- [ ] **Step 3: Verify:** `cd web && npx tsc --noEmit && npx eslint app && npm run build` all pass.
- [ ] **Step 4: Commit** `feat: AM report page`.

### Task 8: Wire-up, docs and end-to-end check

**Files:** Modify `.env.example` (add `SDF_READONLY_DB_URL=` with a one-line comment), `docs/function.md` (new section for the six modules), `launch-app.sh` is unchanged.

- [ ] **Step 1:** Update `.env.example` and `docs/function.md`.
- [ ] **Step 2: Real run:** start the API with the real `.env`, call generate for the current week, export, open the `.docx`, and compare each picture with SD Friday's workload grid for the same week and people. Record any mismatch.
- [ ] **Step 3: Safety grep:** confirm the connection string and password appear in no log, response, or git-tracked file (`git grep` for the host and for `SDF_READONLY_DB_URL=` with a value).
- [ ] **Step 4: Full checks:** pytest, `tsc`, `eslint`, `npm run build` all pass.
- [ ] **Step 5: Commit** `docs: AM report notes and env example`. Do not push without the owner's go-ahead.

---

## Self-review

- **Spec coverage:** header (Task 4, 5), pictures per person for both weeks (3, 6), bullets and blockers (5), blanks and highlighting (4), read-only and secrecy (1, 6, 8), "Weekly Updates Added" blank (4: left blank), page and menu (7), sample untouched (4, 6), open questions defaulted (5 settings). Gap: none found.
- **Types:** `fetch_tasks`/`fetch_people` shapes used consistently in Tasks 2, 5, 6; `render_row` signature matches its use in Task 6.
- **Proportion:** about 1.5× the spec, mostly signatures and test names.
