# Account Manager Report automation: design

Status: **draft for approval**. Nothing is built yet. Date: 2026-10-21.

## Intent

Every Friday by 4:00 PM the Account Manager (Mimi) hands the COO (Jonas) the "Account Manager End-of-Week Report & Sync Prep", a Word document. The sample is `docs/15 (16.10) - Account Manager Report & Sync Prep.docx`. Today she retypes the answers and pastes screenshots by hand. Most of what she writes already lives in SD Friday, the agency's work-tracking app (source: `/home/levi/Desktop/Projects/digital-timesheet`).

This adds a page to the existing Weekly Update web app that pulls the data from SD Friday, fills the real Word template, and gives her a `.docx` to review and send. **Whatever SD Friday can't supply stays blank** for the CS team to type in. The goal is automation: as much of the report as possible is filled without a person.

## Goals

- One click produces a `.docx` that looks exactly like the sample, filled with this week's data.
- The report keeps the sample's **content**: same sections, same questions, same wording, same bullets, same signature table. Its **look** may be better than the sample (the product owner said "or better appearance"), in the Saigon Digital style.
- Workload pictures drawn by Python replace the screenshots she pastes by hand.
- Blank fields are easy to see and fill in before sending.
- Read-only access to SD Friday, with the credential never reaching the browser or git.

## Non-goals

- Writing to SD Friday in any way.
- Sending the report, or a review/approve flow for the COO.
- Editing the template's questions inside the app (a template change means a new `.docx`).
- Hosting online. It runs locally on Mimi's Mac, like the rest of the tool.
- Other SD Friday data (finance, sales, leave details).

## Anti-goals (a failure even if it technically works)

- Any credential with more power than reading three tables.
- A document whose sections, questions or order differ from the sample the COO knows. (A cleaner look is fine.)
- Invented text. If the data isn't there, the field is blank, not guessed.
- Leaking the connection string or the people's emails.

## Decisions already made (by the product owner)

- The sample `.docx` defines the content: its sections, prompts and bullets stay the same. The appearance may be improved.
- Python draws the workload pictures, in the style of SD Friday's workload grid (rows are people, columns are days, a bubble per day).
- The pictures cover **this week and next week**.
- Fields that can't be pulled stay empty for the CS team.
- SD Friday has no public API. Access is a read-only Postgres login, `wut_readonly`, created by the owner in Supabase and already tested: it reads `tasks`, `projects`, and a few `profiles` columns, and nothing else. The connection string is `SDF_READONLY_DB_URL` in `.env` (gitignored).
- Later, an SD Friday MCP token (`https://friday.saigon.digital/api/mcp`, bearer `sdf_…`) is a possible replacement. Nothing here depends on it.

## Data: what is filled from SD Friday

| Report part | Filled? | How |
|---|---|---|
| Header: submitter, reviewer, due date | Yes | Submitter and reviewer from Settings (the sample says "Nguyen" and "Jonas (COO)"), and the coming Friday's date |
| A. Developer Task Lock-In | Yes | Workload pictures for the developers listed in Settings (the sample has two, one per person) |
| A. Scope Creep and Upsell; Cross-Department Handovers | No | Blank |
| B. Last week / This week client bullets (`Client: status`) | Mostly | Per project, from `tasks` (see below) |
| B. Blocker Resolution | Partly | Tasks in status Stuck or On Hold listed; mitigation blank |
| B. Weekly Updates Added to SD Friday (Yes/No) | Not yet | The source is `activity_log`, which `wut_readonly` can't read. Blank until that grant exists |
| C. Lead Alignment; Tooling | No | Blank. Note the sample's three pictures sit under *Lead Alignment*, just before Task Delegation Audit; they show the SEO people's next-week queues, so they are replaced by the SEO pictures there |
| C. Task Delegation Audit | Yes | Workload pictures for the SEO people listed in Settings (the sample has three, one per person); people with no hours that week are flagged |
| Townhall presentation; meeting links | No | Blank |
| WFH / In-office roster | No | SD Friday only has leave types (sick, annual, unpaid, other). Blank |
| Signature table | No | Blank |

### What the sample's five pictures are

Each is a crop of SD Friday's workload grid (dark theme): **one person's row**, Monday to Friday plus two weekend dots, with the name and "Nh/day expected" on the left. Two sit under *Developer Task Lock-In* (Le Minh Tri, Vi Nguyen) and three under *Lead Alignment* (SEO team members, for example Thang Dam Quyet and Nguyen Nguyen Thi My). So the generator makes **one row image per person per week**, replacing those images in place, with the same look.

### Workload picture

From SD Friday's own chart code (`components/workload/WorkloadChart.tsx` and `app/api/workload/tasks/route.ts`):

- Each task has phases (do, peer review, QA, publish), each with a person, start and due date, and an estimate in hours. The person responsible depends on the task's status.
- Remaining hours (estimate minus time tracked) are spread evenly over the weekdays between the phase's start and due date. Weekends get nothing.
- A person's day is the sum over their tasks.
- Bubble size grows with hours against expected hours. Colours: grey for 0, blue under expected, green exactly on expected, red over.
- Expected hours per day come from `profiles.expected_hours` (default 7).
- **Who appears:** a roster in Settings, one list for Development and one for SEO, filled with the sample's names. `profiles.department` can't be used alone, because it holds DEV for one active person and SEO for three, while the sample shows two developers and three SEO people (some people have no department).

Python reimplements this on the rows from `tasks`, `projects` and `profiles`, using matplotlib (already in the project). Each person gets one row image for this week and one for next week (the product owner asked for both). The row looks like the sample's: dark background, bubbles Monday to Friday, two weekend dots. Writing and checking this logic is the main job; it must match SD Friday's grid for the same week.

### Client bullets

The sample's *This week* list is `Client: status` lines. Its *Last week* list is looser: dated items such as "Kenno feedback if any (7.10)". We produce one line per project for both lists, and treat the output as a **draft the CS team edits**, not final text.

Source: tasks grouped by project for this week (Last week) and next week (This week), mapped to Planned / In Progress / QA / Completed as defined in SD Friday's `docs/account-manager-weekly-updates-spec.md`. Only projects flagged `needs_weekly_update` belong in the list, but that flag is in `project_analytics`, which `wut_readonly` can't read yet, so the first version lists projects that had tasks in the period. 

## How it works

1. **Backend (FastAPI, `server.py`):**
   - A small SD Friday client opens `SDF_READONLY_DB_URL` and runs only `select` statements, with fixed queries.
   - `POST /api/am-report/generate` takes the week and returns the filled values and the picture file names.
   - `GET /api/am-report/pictures/{name}` serves a picture.
   - `POST /api/am-report/export` returns the `.docx`.
   - All behind the existing sign-in gate. Without the connection string, the page says so and nothing runs.
2. **Building the document:** the questions and headings are stored as data, copied word for word from the sample. python-docx writes a new `.docx` from that data in a cleaner Saigon Digital style (navy headings, brand font, comfortable spacing, a tidy header block and signature table), with the generated pictures under their sections. Anything unfilled is shown as an empty line with a yellow highlight so it can't be missed. The sample file in `docs/` is the reference for wording and order and is never modified.
3. **Page (Next.js):** a new "AM Report" page reached from the account dropdown. Pick the week (default: the current one), press Generate, review each filled section in a form, edit or fill blanks, then Download `.docx`. Edits are kept in the page for the session.
4. **Settings:** the connection string is not entered in the UI in this version (it is set in `.env`, like the Gemini key). Whether to add it to the Settings dialog is left to the builder.

## Filling the template: rules

- **Never keep last week's answers.** The sample holds answers from 16/10 ("None" under Blocker Resolution, "Yes" under Weekly Updates, "Nein." under the roster, the CRCC Asia banner note under Scope Creep, and the dated bullets). Every answer area is cleared, then either filled from data or left as an empty highlighted line. A stale "Yes" would be invented text.
- **Bullets** in the sample are manual list formatting (the paragraphs use the "normal" style with numbering properties), so new bullets copy the formatting of an existing bullet paragraph rather than relying on a style.
- **Blockers:** one bullet per task in Stuck or On Hold status, written `Task name (Project): status`. It covers all projects, and names come from `full_name` only. The mitigation line stays blank.
- **Weeks:** the page picks a Monday to Friday week, default the current one (the report is due Friday). *This week* is the picked week and *Last week* is the one before; the pictures show the picked week and the following one.
- **Header:** submitter and reviewer are filled from Settings, which start as the sample's "Nguyen" and "Jonas (COO)". The date is the coming Friday.

## Constraints

- Read-only everywhere. Queries are fixed `select` statements; no user text is put into SQL.
- The connection string and the people's emails are never logged, printed, returned by the API, or sent to the browser. Names come from `full_name` only.
- The sample `.docx` stays untouched and in git as the wording reference. The output goes in `out/`, which is gitignored.
- One user, one Mac. No new hosting. The port stays 3000 because of the Google sign-in redirect.
- Python libraries added: `psycopg[binary]` (already tested here) and `python-docx` (already in `requirements.txt`).

## Left to the builder

- Exact query shapes, and how to test the workload maths against SD Friday's grid.
- How to find each prompt in the template reliably, and how to place the pictures.
- The page layout, within the existing design.
- Whether to add the connection string to the Settings dialog.
- How the week boundaries are chosen (Monday to Friday is assumed).

## My calls (not yet confirmed by the product owner)

- The pictures show Monday to Friday and use the department filter: Development for A, SEO for C.
- Highlighting blank fields in yellow.
- Dark-theme row images, matching the sample.
- The document is built from scratch with the sample's wording, not by editing the sample, which also avoids relying on paragraph positions.
- "Last week" means last week's tasks and "This week" means this week's; the exact wording in the sample is "Last week" and "This week" for client progress, and I am assuming that maps to tasks active in those weeks.
- The page is reached from the account dropdown, next to Voice rules.
- Roster in Settings (not `profiles.department`) decides who is in each picture.
- Rules in "Filling the template" above, including clearing every sample answer.
- Bullets for the first version are built from task names and statuses with no AI rewriting. Whether to add Gemini is an open question for the product owner (below).

## Open questions for the product owner

1. **Who is the submitter?** The sample says "Submitted by: Nguyen" but the signature table says Mimi Pham, Account Manager.
2. **AI-written bullets?** Should the client bullets be written by Gemini (the key already used for the SEO report) from the task names and statuses, or stay plain task lists the CS team rewrites? Gemini gives nearer-final sentences but sends project and task names to an outside service.

## Open items that depend on access

- `activity_log` and `project_analytics`: two more read grants would fill the "Weekly Updates Added to SD Friday" answer and the `needs_weekly_update` project filter. Ask the owner.
- Whether task names read well as client bullets: judge on the first real run.

## How we'll know it works

- The generated picture matches SD Friday's workload grid for the same week and people.
- The generated `.docx` opens in Word, looks clean and on brand, and every blank is highlighted.
- The generated `.docx` contains every section, question and bullet of the sample, in the same order, with the same wording.
- A run with the connection string missing or wrong fails with a clear message and writes nothing.
- No secret appears in logs, API responses or git.
