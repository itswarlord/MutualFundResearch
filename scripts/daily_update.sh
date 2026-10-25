#!/usr/bin/env bash
# ==============================================================================
# daily_update.sh - Automated daily cron update script for Indian Mutual Fund Research
# Executes every weekday after AMFI NAV publishing (23:30 IST / 18:00 UTC)
# ==============================================================================

set -euo pipefail

# Determine repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

LOG_FILE="$REPO_ROOT/data/daily_sync.log"
echo "========================================================" >> "$LOG_FILE"
echo "Starting Daily Mutual Fund Sync: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$LOG_FILE"
echo "========================================================" >> "$LOG_FILE"

# Run Python Pipeline (zero external dependencies)
/usr/bin/python3 "$REPO_ROOT/src/main.py" --sync >> "$LOG_FILE" 2>&1

echo "Daily Sync Completed Successfully: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$LOG_FILE"
