#!/bin/bash
# usage: capped.sh MEM MINUTES cmd...
# Runs cmd with a time limit, and with a memory cap when a user systemd scope is available.
# OOMPolicy=continue: an OOM kill ends only the process that hit the cap (a runaway mutant), not the whole run.
set -euo pipefail
mem=$1
minutes=$2
shift 2
if systemd-run --user --scope -q true 2>/dev/null; then
  exec systemd-run --user --scope -q -p "MemoryMax=$mem" -p MemorySwapMax=0 -p OOMPolicy=continue timeout "${minutes}m" "$@"
fi
exec timeout "${minutes}m" "$@"
