#!/bin/bash
# Removes the weekly background job. Leaves the script and the spreadsheet alone.
set -euo pipefail

LABEL="com.a11ytracker.weekly"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$PLIST"
echo "Weekly job removed. The script and spreadsheet are untouched."
