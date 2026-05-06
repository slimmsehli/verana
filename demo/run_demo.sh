#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[demo] Preparing demo MCP config"
cp demo/config/mcp_servers.demo.yaml config/mcp_servers.yaml

echo "[demo] Running baseline EDA testcase (expected to expose bug)"
make -C demo/rtl_case clean || true
if ! make -C demo/rtl_case all; then
  echo "[demo] Testcase failed as expected (bug present)."
fi

echo "[demo] Launch agent command examples:"
echo "  ./venv/bin/rtl-agent run --mode debug --skills rtl_debug,waveform_analyzer"
echo
echo "Suggested prompt:"
echo "  Compile and debug demo/rtl_case. Use available EDA and waveform tools to identify the root cause, propose a fix, and provide verification steps."

