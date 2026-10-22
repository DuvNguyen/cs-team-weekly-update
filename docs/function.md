# Function reference

What each file in `weekly-update-tool` does. Section 1 is the original command-line tool. Sections 2 to 4 are what was added for the web UI. Section 5 is the frontend.

Set `WUT_DEMO=1` to run the whole flow on fake data, with no Google sign-in and no Gemini calls.

## 1. Original tool

`run.py` and `weekly-report.command` still work as before. `run.py` is the reference for the flow. One line in `gsc.py` changed: average position now keeps one decimal (11.1, not 11), so it matches Search Console.

| File | Function | What it does |
|---|---|---|
| `auth.py` | `_credentials(config)` | Desktop Google sign-in. Reuses `token.json`, refreshes it, or opens the browser the first time. Only the command-line flow uses it now. |
| | `get_services(config)` | Builds the Search Console, Sheets, Docs and Drive clients, plus the Gemini client. |
| `dates.py` | `report_period(today)` | The 14 days ending 2 days ago. |
| | `prev_period(start)` | The 14 days before that, for comparison. |
| `gsc.py` | `fetch(service, property, start, end)` | Pulls daily clicks, impressions, CTR and position from Search Console (web search type). |
| | `parse(rows)` | Totals the rows. CTR to one decimal, position is impression-weighted to one decimal. |
| `chart.py` | `render(series, title, out_path)` | Draws the PNG: four stat tiles plus a clicks and impressions line chart. |
| `updates.py` | `fetch_rows(...)` / `match(rows, client_name)` | Reads the SEO team's sheet tab and finds that client's "this week" and "next week" notes. |
| `trends.py` | `for_category(gemini, category, model)` | Optional industry-trend note per category (Gemini with Google Search). Off unless `include_industry_trends` is true. |
| `voice.py` | (data only) | The original writing-style text (`VOICE`, `EXAMPLES`). It is now the factory default that `voice_store.py` parses. |
| `report.py` | `build_prompt(...)` | Builds the Gemini prompt from the numbers, the notes and `voice.VOICE` / `voice.EXAMPLES`. |
| | `summarize(...)` | Calls Gemini and returns the paragraph (the UI uses `pipeline._generate` instead). |
| | `compose_body(...)` | Joins the paragraph, the SEO notes and the optional trend note. |
| | `create_doc` / `append_client` / `doc_url` | Create the Google Doc, add each client, build the link. The UI no longer calls them. |
| `list_sites.py` | (script) | Lists the Search Console properties the signed-in account can see. Useful for 403 errors. |

## 2. Web backend

### `pipeline.py` (the job engine)

| Function | What it does |
|---|---|
| `load_config()` / `public_config()` | Reads `config.json` (the `GEMINI_API_KEY` env var wins). The public version hides secrets. |
| `save_clients(clients)` | Writes the client list back to `config.json`. |
| `services(config, email=None)` | Google and Gemini clients. With an email it uses that signed-in user's tokens. Without one it uses the old desktop flow. Cached per user. |
| `forget(email)` | Drops that user's cached clients (called on sign-out). |
| `list_tabs(email)` | Sheet tab names for the dropdown. |
| `latest_data_date(email)` | The newest day Search Console has data for (tries clients until one is readable, cached 30 minutes). The shortcuts end there, like Search Console's own date picker. |
| `default_period()` | Fallback dates when the API check is unavailable. |
| `new_job(tab, clients, start, end, email, style_id)` | Starts a background job, one preview per client, owned by `email`, written in the chosen style. |
| `generate_client(job, c, config, svc)` | One client: Search Console data, chart, Gemini summary, then the email. Also used by Retry. |
| `_prompt(style, ...)` / `_generate(gemini, prompt)` | Build the prompt in a given style (swaps `voice.VOICE` under a lock) and call Gemini. |
| `_assemble(config, cfg, c, summary, ctx)` | Builds the client email parts: "Hi {contact}," (or "Hi {client} team," when no greeting name is set), the sections, SEO notes / trend, and "Best regards, {sender}". Uses `contact` and `sender` from `config.json` if set. |
| `regenerate_client(job, name, instruction, style_id)` | Rewrites one email from the stored numbers, steered by the prompt and optionally another style. |
| `retry_client(job, name)` / `chart_path(job, name)` / `view(job)` | Re-run one client, chart file path, job without private fields. |
| `analyze_style(email_text)` | Drafts a writing style from a pasted email (nothing is saved). |
| `export_docx(job)` | Builds the Word file (python-docx): one page per client, chart, email text with clickable links. |
| `publish(job)` | Creates a Google Doc. The UI no longer calls it. |

### `server.py` (FastAPI)

Every `/api/*` route except `/api/auth/*` needs a valid session. A job can only be read by the user who started it.

| Route | What it does |
|---|---|
| `GET /api/config` / `PUT /api/clients` | Public config; save the client list. |
| `GET /api/period` | Latest Search Console data date. |
| `GET /api/tabs` | Sheet tab names. |
| `POST /api/jobs`, `GET /api/jobs/{id}` | Start a job (`tab, start, end, clients, style_id`); poll it. |
| `GET /api/jobs/{id}/chart/{name}` | The chart PNG. |
| `PATCH /api/jobs/{id}/clients/{name}` | Save edited email text or the include flag. |
| `POST .../clients/{name}/retry` / `.../regenerate` | Re-run a client; rewrite its email (`prompt`, `style_id`). |
| `POST /api/jobs/{id}/export` | Download the Word file. |
| `POST /api/jobs/{id}/publish` | Create a Google Doc (unused by the UI). |
| `GET/PUT /api/voice` | Read and save all writing styles. |
| `POST /api/voice/analyze` / `POST /api/voice/reset` | Draft a style from an email; restore the original style. |

## 3. Sign-in and sessions

### `auth_web.py` ("Sign in with Google", OAuth 2.0 code flow with PKCE)

| Piece | What it does |
|---|---|
| `GET /api/auth/login` | Makes `state` and a PKCE verifier (10-minute HttpOnly cookie), redirects to Google. |
| `GET /api/auth/callback` | Checks `state`, exchanges the code, verifies the ID token, checks all permissions were granted, saves the user's Google token, starts a session. |
| `GET /api/auth/me` / `POST /api/auth/logout` | Who is signed in; end the session and delete that user's Google token. |
| `require_user` | The gate used by every API route (demo mode skips it). |
| `credentials_for(email)` | Loads and refreshes a user's Google credentials. Raises `NotSignedIn` (HTTP 401) if they are gone or revoked. |

Settings: `WUT_PUBLIC_URL` (default `http://localhost:3000`, also turns on Secure cookies for https) and optional `WUT_ALLOWED_DOMAINS` (e.g. `saigon.digital`).

### `sessions.py`

| Function | What it does |
|---|---|
| `create(user)` / `get(sid)` / `delete(sid)` | 30-day sessions. The cookie holds a random 256-bit id; only its SHA-256 hash is stored in `data/sessions.json`. |
| `save_token` / `load_token` / `delete_token` | One Google token file per account in `data/tokens/` (mode 600). |

`data/` is gitignored.

## 4. Writing styles

### `voice_store.py` (`data/voice.json`)

A style is `{id, name, persona, style[], avoid[], examples[]}`. One style is the default.

| Function | What it does |
|---|---|
| `default()` / `default_style()` | Parses the factory text in `voice.py` into one style ("Mimi (original)"). |
| `load()` / `save(v)` / `reset()` | Read, validate and write `data/voice.json`; reset restores the original. Old single-style files are migrated. |
| `validate(v)` | Trims, drops empty rows, enforces limits and unique names. |
| `get_style(id)` | A style by id, or the default. |
| `render(style)` | Turns a style into the two strings `report.build_prompt` reads. |
| `analyze(gemini, model, email)` | Gemini reads a pasted email and returns a drafted style (name, opening line, style rules, avoid rules, the email kept as an example). Returned for review, never saved automatically. |

## 5. Frontend (`web/app`, Next.js)

Pages are real routes. Layouts persist across navigation and Next's Cache Components keeps each page's state, so edits survive switching tabs.

| Route | File | What it shows |
|---|---|---|
| `/` | `page.tsx` | Redirects to `/setup`. |
| `/setup` | `setup/page.tsx` | Period, notes tab, email style, clients. |
| `/report` | `report/page.tsx` | Generation progress, review, Word download. |
| `/voice` | `voice/page.tsx` | Writing styles. |

| File | What it holds |
|---|---|
| `layout.tsx` | Fonts (Space Grotesk, Be Vietnam Pro) and the shared shell. |
| `components/shell/app-shell.tsx` | Sign-in gate, plus shared state through `useApp()`: user, config, current job. |
| `components/shell/header.tsx` | One-line header: wordmark, steps, Voice rules, account, sign out. |
| `components/report/setup.tsx`, `setup-screen.tsx` | The Setup form and its page wrapper. |
| `components/report/run.tsx`, `report-screen.tsx` | Progress, client cards, floating download bar; page wrapper. |
| `components/report/client-card.tsx`, `email-dialog.tsx`, `stats.tsx` | Compact client card; full email editor with style switch and regenerate-with-prompt; stat tiles. |
| `components/report/client-picker.tsx` | All clients as tickable rows with filter, Select all, Clear. |
| `components/report/voice-manager.tsx` | Style list, editor, add from email or by hand, save/reset bar. |
| `components/report/login.tsx`, `stepper.tsx` | Login screen; Setup / Generate / Review links. |
| `components/ui/` | Hand-built `combobox`, `listbox`, `checkbox`, `card`, `feedback` (Badge, Alert, Skeleton). `multi-combobox.tsx` and `chip.tsx` are no longer used. |
| `lib/api.ts`, `lib/job.ts`, `lib/period.ts` | Typed backend calls (with `ApiError` carrying the status); job-state helper; date helper. |
| `globals.css`, `styles/` | Saigon Digital design tokens, custom scrollbar, buttons, animations. `design.md` (the old Wabi-Sabi spec) is superseded. |

## Files and settings that are not code

| Item | Notes |
|---|---|
| `config.json` | Clients, sheet and Drive ids, keys. Optional per-client `contact` (the greeting name, set on the Clients page); optional top-level `sender`. Gitignored. |
| `.env` | `GEMINI_API_KEY` copy (the app prefers it). Gitignored; `.env.example` is committed. |
| `client_secret.json` | The Google OAuth client (app identity). Gitignored. |
| `data/` | Sessions, per-user Google tokens, `voice.json`. Gitignored. |
| `token.json` | Old desktop-flow token. No longer used by the web app. |

## 6. Account Manager report

The weekly "Account Manager End-of-Week Report & Sync Prep" `.docx`, built from SD Friday (read-only). Design: `docs/superpowers/specs/2026-10-21-am-report-automation-design.md`.

| File | What it does |
|---|---|
| `sdf.py` | Read-only Postgres client for SD Friday (`SDF_READONLY_DB_URL`). `fetch_tasks`, `fetch_people` (no emails), `fetch_projects`. Fixed SELECTs only. |
| `workload.py` | Hours per person per weekday, ported from SD Friday's workload grid (`daily_hours`, `bubble_status`). |
| `workload_pic.py` | `render_row` draws one person's row as a PNG, in SD Friday's dark grid style. |
| `am_bullets.py` | Client bullets per week (`client_bullets`), blockers, status groups, and roster matching. |
| `am_settings.py` | Submitter, reviewer and the two rosters (developers, SEO), saved in `data/am_settings.json`. |
| `am_template.json` | The sample report's headings and prompts, word for word. |
| `am_docx.py` | `build` writes the styled `.docx`; unfilled prompts get a yellow-highlighted empty line. `blank_prompts` lists them. |
| `am_web.py` | API: `GET/PUT /api/am-report/settings`, `POST /generate`, `GET /pictures/{week}/{name}`, `POST /export`. |

Page: `web/app/am-report` (reached from the account dropdown). Output goes in `out/am-report/`.
