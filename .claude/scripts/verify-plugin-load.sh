#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

checks=(
  "/develop smoke-test"
  "/ship"
  "/preflight"
  "/hotfix smoke-test"
  "/evolve-workflow ."
  "/iterate-workflow --dry-run ."
  "/review"
  "/test"
  "/commit"
  "/doc"
  "/workflow-audit"
)

pass=0
fail=0

for cmd in "${checks[@]}"; do
  output="$($CLAUDE_BIN -p --plugin-dir "$PLUGIN_ROOT" --output-format json "$cmd" 2>&1 || true)"
  if [[ "$output" == *"Unknown skill:"* ]] || [[ "$output" == *"Unknown command"* ]]; then
    echo "[FAIL] $cmd -> not discovered"
    fail=$((fail + 1))
  elif [[ "$output" == *"Not logged in · Please run /login"* ]] || [[ "$output" == *'"subtype":"success"'* ]]; then
    echo "[PASS] $cmd -> discovered"
    pass=$((pass + 1))
  else
    echo "[FAIL] $cmd -> unexpected response"
    echo "$output"
    fail=$((fail + 1))
  fi
done

echo "PASS: $pass"
echo "FAIL: $fail"

if [[ $fail -ne 0 ]]; then
  exit 1
fi
