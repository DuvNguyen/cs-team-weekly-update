#!/bin/bash
# Double-click me to remove Weekly Update's app, Dock icon and downloaded libraries (frees disk space).
# Your own files stay: client_secret.json, .env, config.json, data/ and out/.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

APP="$HOME/Applications/Weekly Update.app"
DOCK_PLIST="$HOME/Library/Preferences/com.apple.dock.plist"

echo "=================================="
echo "   Weekly Update — uninstaller"
echo "=================================="
echo ""
echo "This will:"
echo "  • stop Weekly Update if it is running"
echo "  • remove it from the Dock and delete the app"
echo "  • delete the installed libraries (Python .venv, web/node_modules, web/.next)"
echo "Your secrets, settings and reports are kept."
echo ""
read -r -p "Continue? [y/N] " ANSWER
case "$ANSWER" in y|Y|yes|YES) ;; *) echo "Cancelled."; exit 0 ;; esac

echo ""
echo "▶ Stopping the app"
for f in .run/api.pid .run/web.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null; done
for port in 8000 3000; do   # also catch child processes — but only ones that belong to this folder
  for pid in $(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null); do
    cwd="$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
    case "$cwd" in "$PROJECT_DIR"|"$PROJECT_DIR"/*) kill "$pid" 2>/dev/null ;; esac
  done
done

echo "▶ Removing it from the Dock"
if [ -f "$DOCK_PLIST" ]; then
  i=0
  while PB=$(/usr/libexec/PlistBuddy -c "Print :persistent-apps:$i:tile-data:file-data:_CFURLString" "$DOCK_PLIST" 2>/dev/null); do
    case "$PB" in
      *"Weekly%20Update.app"*|*"Weekly Update.app"*)
        /usr/libexec/PlistBuddy -c "Delete :persistent-apps:$i" "$DOCK_PLIST"; killall cfprefsd 2>/dev/null; continue ;;
    esac
    i=$((i + 1))
  done
  killall Dock 2>/dev/null
fi

echo "▶ Deleting the app"
rm -rf "$APP"

echo "▶ Deleting installed libraries"
BEFORE=$(du -sk .venv venv web/node_modules web/.next 2>/dev/null | awk '{s+=$1} END {print s+0}')
rm -rf .venv venv web/node_modules web/.next .run .env.os_cache
echo "  freed about $((BEFORE / 1024)) MB"

echo ""
echo "✔ Uninstalled. To use the app again, double-click 'Install Weekly Update.command'."
echo "  To remove everything, drag this whole folder to the Trash."
echo ""
read -n 1 -s -r -p "Press any key to close."
echo ""
