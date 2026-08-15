#!/bin/bash
# Installs the accessibility tracker as a weekly background job (macOS launchd).
# Safe to re-run: it replaces any previous install of the same job.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.a11ytracker.weekly"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This installer is macOS only."
  echo "On Linux, add this line to 'crontab -e' instead:"
  echo "  0 9 * * 1 $DIR/run.sh"
  exit 1
fi

# --- 1. Dependencies -------------------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required. Install it with:  brew install gh"
  exit 1
fi

# Sign-in happens here rather than sending people off to read gh's docs: gh opens
# github.com in the browser and prints a one-time code to paste there.
if ! gh auth status >/dev/null 2>&1; then
  echo "You are not signed in to GitHub."
  read -r -p "Open github.com in your browser to sign in now? [Y/n]: " SIGNIN
  case "${SIGNIN:-y}" in
    [Yy]*)
      echo
      echo "gh will ask two short setup questions, then open github.com with a"
      echo "one-time code (copied to your clipboard). Paste it there, then come back."
      echo
      gh auth login --hostname github.com --git-protocol https --web --clipboard
      ;;
    *)
      echo "Skipped. Run 'gh auth login' when you are ready, then re-run install.sh."
      exit 1
      ;;
  esac
  if ! gh auth status >/dev/null 2>&1; then
    echo "Sign-in did not complete. Run 'gh auth login' and try again."
    exit 1
  fi
  echo "Signed in."
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

read -r -p "Which day of the week? [Monday]: " DAY_IN
DAY_IN="${DAY_IN:-monday}"
# launchd numbers weekdays Sunday=0 through Saturday=6. Accept a name, an
# abbreviation, or the number itself.
case "$(echo "$DAY_IN" | tr '[:upper:]' '[:lower:]' | cut -c1-3)" in
  sun|0) WEEKDAY=0; DAY_NAME="Sunday" ;;
  mon|1) WEEKDAY=1; DAY_NAME="Monday" ;;
  tue|2) WEEKDAY=2; DAY_NAME="Tuesday" ;;
  wed|3) WEEKDAY=3; DAY_NAME="Wednesday" ;;
  thu|4) WEEKDAY=4; DAY_NAME="Thursday" ;;
  fri|5) WEEKDAY=5; DAY_NAME="Friday" ;;
  sat|6) WEEKDAY=6; DAY_NAME="Saturday" ;;
  *) echo "Not a day of the week: $DAY_IN"; exit 1 ;;
esac

read -r -p "What time, 24-hour HH:MM [09:00]: " TIME_IN
TIME_IN="${TIME_IN:-09:00}"
if ! [[ "$TIME_IN" =~ ^([0-9]{1,2}):?([0-9]{2})?$ ]]; then
  echo "Time must look like 09:00 or 14:30."
  exit 1
fi
HOUR=$((10#${BASH_REMATCH[1]}))
MINUTE=$((10#${BASH_REMATCH[2]:-0}))
if (( HOUR > 23 )) || (( MINUTE > 59 )); then
  echo "Time must be between 00:00 and 23:59."
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

    <!-- Weekly. If the Mac is asleep at this time, launchd runs the job on wake. -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>$WEEKDAY</integer>
        <key>Hour</key>
        <integer>$HOUR</integer>
        <key>Minute</key>
        <integer>$MINUTE</integer>
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

# --- 5. Prove it works now rather than next week --------------------------
echo "Running once to verify..."
launchctl kickstart -p "gui/$UID_NUM/$LABEL" >/dev/null

# Wait for the job to finish, then read its exit code. Waiting on the log file
# instead would return immediately on a re-install, since the log already exists.
# launchd reports "(never exited)" until the run completes, so require a number.
EXIT_CODE=""
for _ in $(seq 1 90); do
  INFO="$(launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null || true)"
  if grep -q "state = not running" <<<"$INFO"; then
    EXIT_CODE="$(awk -F'= ' '/last exit code/ {print $2}' <<<"$INFO" | tr -d ' ')"
    [[ "$EXIT_CODE" =~ ^[0-9]+$ ]] && break
  fi
  sleep 1
done
if [[ "$EXIT_CODE" == "0" ]]; then
  echo
  printf "Installed. Tracking '%s' every %s at %02d:%02d.\n" "$OWNER" "$DAY_NAME" "$HOUR" "$MINUTE"
  tail -1 "$DIR/a11y-tracker.log"
  echo "Spreadsheet: $DIR/accessibility-issues.xlsx"
  echo "To remove:   $DIR/uninstall.sh"
else
  echo
  echo "The job was installed but the test run failed (exit $EXIT_CODE)."
  echo "See $DIR/launchd.err.log and $DIR/a11y-tracker.log"
  exit 1
fi
