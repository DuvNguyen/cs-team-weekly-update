#!/bin/bash
# Weekly SEO Report — just double-click me.
# Works from any folder on the Mac. First run sets itself up; after that it just runs.
cd "$(dirname "$0")" || exit 1

echo "=================================="
echo "   Weekly SEO Report"
echo "=================================="
echo ""

# macOS can block access to folders on the Desktop/Documents/Downloads.
# If a command fails with "Operation not permitted", explain it instead of a cryptic error.
show_permission_help() {
  echo ""
  echo "macOS is blocking this tool from reading its own folder."
  echo "This happens when the folder is on your Desktop, Documents or Downloads."
  echo ""
  echo "Easiest fix — move the folder, then try again:"
  echo "  1. Close this window."
  echo "  2. Drag the 'weekly-update-tool' folder out of Desktop/Documents/Downloads"
  echo "     to somewhere like your Home folder."
  echo "  3. Double-click weekly-report.command again."
  echo ""
  echo "Alternative — let Terminal read those folders once:"
  echo "  System Settings → Privacy & Security → Full Disk Access"
  echo "  → turn ON 'Terminal', then quit and reopen Terminal."
}

# 1. Need Python 3 (macOS installs it with the developer tools).
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 isn't installed yet."
  echo "A macOS window should pop up to install the developer tools —"
  echo "click Install, wait for it to finish, then double-click this file again."
  xcode-select --install 2>/dev/null
  echo ""
  read -n 1 -s -r -p "Press any key to close."
  exit 1
fi

# 2. First run only: build the venv and install the libraries (~1-2 min, once).
if [ ! -d "venv" ]; then
  echo "First-time setup: installing what this needs (about 1-2 minutes)."
  echo "This happens only once — please wait…"
  echo ""
  python3 -m venv venv || { echo "Could not create the environment."; read -n1 -s -r -p "Press any key."; exit 1; }
  ./venv/bin/python -m pip install --quiet --upgrade pip
  if ! ./venv/bin/python -m pip install --quiet -r requirements.txt; then
    echo ""
    echo "Library install failed. Check the internet connection and double-click again."
    read -n1 -s -r -p "Press any key to close."
    exit 1
  fi
  echo "Setup complete."
  echo ""
fi

# 3. Build the report (-u = show progress live; tee keeps it visible while logging).
LOG="$(mktemp /tmp/weekly-report.XXXXXX)"
./venv/bin/python -u run.py 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
if [ $STATUS -ne 0 ]; then
  if grep -qi "Operation not permitted" "$LOG"; then
    show_permission_help
  fi
  echo ""
  read -n 1 -s -r -p "Something went wrong — press any key to close this window."
  rm -f "$LOG"
  exit 1
fi
rm -f "$LOG"

echo ""
read -n 1 -s -r -p "All done — press any key to close this window."
echo ""
