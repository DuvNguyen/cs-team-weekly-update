# Bi-weekly SEO Report — how to run it

## Every 2 weeks

1. **Unzip** the folder somewhere easy to find. **Avoid Desktop, Documents and Downloads** — macOS protects those folders and can block the tool there. Your Home folder is a safe spot.
2. **Open the folder.**
3. **Set the current SEO tab** in `config.json` (see the next section).
4. **Double-click `weekly-report.command`.**
5. A black Terminal window opens and shows progress, client by client.
   **Just wait** — it takes a few minutes for all the clients.
6. When it finishes, it prints a **Google Doc link** and opens the report in your browser.
   That Doc is your bi-weekly report.

That's it.

## Setting the current SEO tab

The SEO sheet has a new tab every 2 weeks. Tell the report which one to read:

1. In the folder, **double-click `config.json`** → open it with **TextEdit**.
2. Near the top, find this line:

   `"seo_sheet_tab": "20/7-24/7",`

3. Change the dates to **the current tab name**, typed exactly as it appears on the sheet's tab (e.g. `27/7-31/7`). **Keep the quotes and the comma.**
4. **Save** (⌘S) and close.

If you skip this or the name doesn't match a tab, the report still builds — it just won't include the SEO team's notes that time.

## The very first time only

- **Right-click `weekly-report.command` → Open** (instead of double-clicking), then click **Open** in the pop-up. macOS only asks this once; after that you can double-click normally.
- The first run spends **1–2 extra minutes** installing what it needs. This happens only once. Later runs are quicker.

## Good to know

- The window shows a line per client, like `[ 3/30] Acuro … ✓ 984 clicks, 88,284 impressions`. A `⚠ skipped` line just means one client had no data this period — the rest still run.
- The report covers the **last 14 days, ending 2 days ago** (Google Search Console data is ~2 days behind), compared with the 14 days before that.
- When it's done it says **"All done — press any key to close this window."**

## If something looks wrong

- It says **"Python 3 isn't installed"** → click **Install** on the macOS pop-up, wait for it to finish, then double-click again.
- **Library install failed** → check your internet connection and double-click again.
- It says **"macOS is blocking this tool from reading its own folder"** (or shows `Operation not permitted`) → the folder is in a place macOS protects (Desktop, Documents, Downloads). Fix it one of two ways:
  - **Move the folder** somewhere else — your Home folder is fine — then double-click again. Nothing else changes.
  - Or grant Terminal access once: **System Settings → Privacy & Security → Full Disk Access → turn on "Terminal"**, then quit and reopen Terminal.
- Anything else → send a screenshot of the Terminal window to **Tri Dev**.
