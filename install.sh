#!/bin/bash
# Installs the accessibility tracker as a daily background job (macOS launchd).
# Safe to re-run: it replaces any previous install of the same job.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.a11ytracker.daily"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This installer is macOS only."
  echo "On Linux, add this line to 'crontab -e' instead:"
  echo "  0 9 * * * $DIR/run.sh"
  exit 1
fi

# --- 1. Dependencies -------------------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required. Install it with:  brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "You are not logged in to GitHub. Run:  gh auth login"
  exit 1
fi

if ! python3 -c "import openpyxl" >/dev/null 2>&1; then
  echo "Installing openpyxl..."
  python3 -m pip install --user --quiet openpyxl
fi

# --- 2. macOS blocks background jobs from ~/Documents, ~/Desktop, ~/Downloads
case "$DIR" in
  "$HOME/Documents"*|"$HOME/Desktop"*|"$HOME/Downloads"*)
    echo "Warning: this folder is inside a macOS-protected location."
    echo "Background jobs cannot read or write there without Full Disk Access."
    echo "Move this folder somewhere like ~/a11y-tracker and re-run install.sh."
    echo "(Running it by hand works fine from here.)"
    exit 1
    ;;
esac

# --- 3. Who and when -------------------------------------------------------
DEFAULT_OWNER="$(gh api user --jq .login 2>/dev/null || true)"
read -r -p "GitHub username or org to track [$DEFAULT_OWNER]: " OWNER
OWNER="${OWNER:-$DEFAULT_OWNER}"
if [[ -z "$OWNER" ]]; then
  echo "No username given."
  exit 1
fi

read -r -p "Run daily at what hour, 0-23 [9]: " HOUR
HOUR="${HOUR:-9}"
if ! [[ "$HOUR" =~ ^[0-9]{1,2}$ ]] || (( HOUR > 23 )); then
  echo "Hour must be a number from 0 to 23."
  exit 1
fi

# --- 4. Write the launchd job ---------------------------------------------
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$DIR/run.sh</string>
        <string>--owner</string>
        <string>$OWNER</string>
    </array>

    <!-- If the Mac is asleep at this hour, launchd runs the job on wake. -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$HOUR</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>$DIR/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$DIR/launchd.err.log</string>
</dict>
</plist>
PLIST_EOF

chmod +x "$DIR/run.sh" "$DIR/track_a11y.py"

launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$PLIST"

# --- 5. Prove it works now rather than at 9am tomorrow --------------------
echo "Running once to verify..."
launchctl kickstart -p "gui/$UID_NUM/$LABEL" >/dev/null
for _ in $(seq 1 30); do
  if [[ -s "$DIR/a11y-tracker.log" ]]; then break; fi
  sleep 1
done

EXIT_CODE="$(launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null | awk '/last exit code/ {print $NF}')"
if [[ "$EXIT_CODE" == "0" ]]; then
  echo
  echo "Installed. Tracking '$OWNER' every day at $HOUR:00."
  tail -1 "$DIR/a11y-tracker.log"
  echo "Spreadsheet: $DIR/accessibility-issues.xlsx"
  echo "To remove:   $DIR/uninstall.sh"
else
  echo
  echo "The job was installed but the test run failed (exit $EXIT_CODE)."
  echo "See $DIR/launchd.err.log and $DIR/a11y-tracker.log"
  exit 1
fi
