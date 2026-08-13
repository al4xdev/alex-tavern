#!/usr/bin/env bash
# Block until every running repetition battery has finished.
#
# WHY THIS EXISTS. The obvious one-liner polls for the `--exec-one` child:
#
#     while pgrep -f exec-one >/dev/null; do sleep 60; done
#
# A battery has NO such child between replicates. On 2026-08-12 that gap made a
# waiter report DONE while the run was still going, and a session from an older
# battery was scored as if it came from the newer one - two batteries were in
# flight and their output directories interleaved. The mislabel was only caught
# by comparing session mtimes against commit times.
#
# So: watch the PARENT (`-m tools.acceptance.repetition_battery`), which lives
# for the whole run, and refuse to exit on a child gap.
#
#   tools/acceptance/wait_for_battery.sh [timeout_minutes]
#
# Exits 0 when no battery parent remains, 1 on timeout. Prints the sessions
# newest-first so the caller can see what it is about to score.
set -uo pipefail

limit_min="${1:-180}"
deadline=$(( SECONDS + limit_min * 60 ))
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

while true; do
  # -f matches the full command line; the parent runs with `-m`, the child with
  # the script path plus `--exec-one`, so this pattern cannot match the child.
  if ! pgrep -f "[-]m tools.acceptance.repetition_battery" >/dev/null; then
    echo "no battery parent running"
    break
  fi
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "TIMEOUT after ${limit_min}m; battery still running" >&2
    exit 1
  fi
  sleep 60
done

echo "--- sessions, newest first ---"
ls -dt "$repo"/plans/artifacts/repetition-battery/*/sessions/*/ 2>/dev/null | head -8
