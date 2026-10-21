#!/bin/bash
# Weekly update tool — one-click launcher (macOS / Linux).
# Starts the Python API (8000) and the Next.js UI (3000) once, then opens the UI as a Chrome app window.
# Re-running it just opens another window; servers already running are reused.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

API_PORT=8000
WEB_PORT=3000            # fixed: the Google OAuth redirect URI is registered for localhost:3000
STATE_DIR="$PROJECT_DIR/.run"
mkdir -p "$STATE_DIR"
CACHE_FILE="$PROJECT_DIR/.env.os_cache"

# Last-resort fallback so Homebrew's node is found when launched from Finder/Automator.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

fail() { echo "ERROR: $1" >&2; command -v osascript >/dev/null && osascript -e "display alert \"Weekly update tool\" message \"$1\"" >/dev/null 2>&1; exit 1; }

# --- OS + browser command, cached after the first run -----------------------------------------
if [ -f "$CACHE_FILE" ]; then
  # shellcheck disable=SC1090
  source "$CACHE_FILE"
else
  OS_TYPE="$(uname -s)"
  case "$OS_TYPE" in
    Darwin) LAUNCH_CMD='open -na "Google Chrome" --args --app=' ;;
    Linux)  LAUNCH_CMD="$(command -v google-chrome || command -v chromium || command -v chromium-browser) --app=" ;;
    *)      fail "Unsupported OS: $OS_TYPE" ;;
  esac
  printf 'OS_TYPE=%q\nLAUNCH_CMD=%q\n' "$OS_TYPE" "$LAUNCH_CMD" > "$CACHE_FILE"
fi

is_up() { curl -s -o /dev/null --max-time 2 "$1"; }

wait_for() {  # url, seconds
  for _ in $(seq 1 "$2"); do is_up "$1" && return 0; sleep 1; done
  return 1
}

# --- one-time setup ---------------------------------------------------------------------------
[ -x .venv/bin/uvicorn ] || {
  command -v python3 >/dev/null || fail "Python 3 is not installed."
  echo "First run: installing Python libraries…"
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt || fail "Python install failed."
}
command -v npm >/dev/null || fail "Node.js is not installed (https://nodejs.org)."
[ -d web/node_modules ] || { echo "First run: installing UI libraries…"; (cd web && npm install --silent) || fail "npm install failed."; }

# --- API ----------------------------------------------------------------------------------------
if ! is_up "http://127.0.0.1:$API_PORT/docs"; then
  nohup .venv/bin/uvicorn server:app --host 127.0.0.1 --port "$API_PORT" > "$STATE_DIR/api.log" 2>&1 &
  echo $! > "$STATE_DIR/api.pid"
  wait_for "http://127.0.0.1:$API_PORT/docs" 20 || fail "API did not start. See .run/api.log"
fi

# --- UI (production build: much faster than `next dev`; rebuilt only when sources change) ------
if ! is_up "http://127.0.0.1:$WEB_PORT"; then
  if lsof -iTCP:"$WEB_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    fail "Port $WEB_PORT is used by another program. Close it and try again."
  fi
  if [ ! -d web/.next ] || [ -n "$(find web/app web/package.json web/next.config.ts -newer web/.next/BUILD_ID -print -quit 2>/dev/null)" ]; then
    echo "Building the UI (only after updates)…"
    (cd web && npm run build > "$STATE_DIR/build.log" 2>&1) || fail "UI build failed. See .run/build.log"
  fi
  (cd web && nohup npm run start -- -p "$WEB_PORT" > "$STATE_DIR/web.log" 2>&1 & echo $! > "$STATE_DIR/web.pid")
  wait_for "http://127.0.0.1:$WEB_PORT" 30 || fail "UI did not start. See .run/web.log"
fi

[ "$1" = "--no-open" ] && exit 0

# --- open the window ----------------------------------------------------------------------------
eval "$LAUNCH_CMD\"http://localhost:$WEB_PORT\""
