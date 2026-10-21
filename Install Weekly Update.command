#!/bin/bash
# Double-click me once. Installs everything and puts "Weekly Update" in the Dock.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

APP="$HOME/Applications/Weekly Update.app"

pause_exit() { echo ""; read -n 1 -s -r -p "Press any key to close."; echo ""; exit "${1:-0}"; }
step() { echo ""; echo "▶ $1"; }
die()  { echo ""; echo "✖ $1"; pause_exit 1; }

echo "=================================="
echo "   Weekly Update — installer"
echo "=================================="

case "$PROJECT_DIR" in
  "$HOME/Desktop"*|"$HOME/Documents"*|"$HOME/Downloads"*)
    die "This folder is in Desktop/Documents/Downloads, which macOS blocks.
  Drag the 'weekly-update-tool' folder to your Home folder and double-click the installer again." ;;
esac

step "Checking Google Chrome"
[ -d "/Applications/Google Chrome.app" ] || [ -d "$HOME/Applications/Google Chrome.app" ] \
  || { open "https://www.google.com/chrome/"; die "Google Chrome is not installed. Install it from the page that just opened, then run this installer again."; }

step "Checking Python"
if ! command -v python3 >/dev/null 2>&1; then
  xcode-select --install 2>/dev/null
  die "A macOS window should pop up to install developer tools (includes Python). Click Install, wait for it to finish, then run this installer again."
fi

step "Checking Node.js"
if ! command -v npm >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing Node.js with Homebrew…"
    brew install node || die "Node.js install failed."
  else
    open "https://nodejs.org/en/download"
    die "Node.js is not installed. Install it from the page that just opened (macOS Installer), then run this installer again."
  fi
fi

step "Checking the sign-in files"
MISSING=""
for f in client_secret.json .env; do [ -f "$f" ] || MISSING="$MISSING $f"; done
[ -z "$MISSING" ] || die "Missing file(s):$MISSING
  Copy them into this folder ($PROJECT_DIR), then run this installer again."

step "Installing the app (a few minutes the first time — please wait)"
chmod +x launch-app.sh
./launch-app.sh --no-open || die "Setup failed. Details are in the .run folder (api.log / web.log / build.log)."

step "Creating the 'Weekly Update' app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Weekly Update</string>
  <key>CFBundleIdentifier</key><string>digital.saigon.weekly-update</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSUIElement</key><true/>
</dict></plist>
PLIST
printf '#!/bin/bash\nexec "%s/launch-app.sh"\n' "$PROJECT_DIR" > "$APP/Contents/MacOS/launcher"
chmod +x "$APP/Contents/MacOS/launcher"

step "Adding it to the Dock"
if ! defaults read com.apple.dock persistent-apps 2>/dev/null | grep -q "Weekly Update.app"; then
  defaults write com.apple.dock persistent-apps -array-add \
    "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>file://$APP/</string><key>_CFURLStringType</key><integer>15</integer></dict></dict></dict>"
  killall Dock
fi

echo ""
echo "✔ All done! Opening Weekly Update… From now on, click it in the Dock."
open "$APP"
pause_exit 0
