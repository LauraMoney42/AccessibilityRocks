#!/bin/bash
# Wrapper used by launchd (and fine to run by hand). launchd starts jobs with a
# minimal PATH, so the Homebrew locations for gh and python3 are spelled out here.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1
python3 track_a11y.py "$@" >> "$DIR/a11y-tracker.log" 2>&1
