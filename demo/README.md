# Demo Testcase and MCP Integration

This demo shows how `rtl-agent` can integrate with multiple MCP servers and use EDA tools for compile/debug/verification workflows.

## Included Demo Components

- `demo/mcp/simple_mcp_server.py`
  - basic text/file tools for demonstration
- `demo/mcp/eda_mcp_server.py`
  - wraps `verilator` and `yosys`
- `demo/mcp/waveform_mcp_server.py`
  - parses VCD and exposes signal query tools
- `demo/mcp/terminal_mcp_server.py`
  - executes Linux shell commands within a restricted workspace root
- `demo/rtl_case/`
  - intentionally buggy RTL + testbench
  - Makefile for lint/build/run/yosys
- `demo/config/mcp_servers.demo.yaml`
  - MCP server config for this demo (including `terminal-tools`)
- `demo/run_demo.sh`
  - helper script for setup and baseline run

## Prerequisites

- Python environment with `rtl-agent` installed
- `verilator` in PATH
- `yosys` in PATH

## Quick Start

From project root:

```bash
chmod +x demo/run_demo.sh
./demo/run_demo.sh
```

Then start the agent:

```bash
./venv/bin/rtl-agent run --mode debug --skills rtl_debug,waveform_analyzer --confirm-terminal
```

Suggested prompt:

```text
Compile and debug demo/rtl_case. Use available EDA and waveform tools to identify the root cause, propose a fix, and provide verification steps.
```

## Notes

- The demo DUT intentionally has a bug (missing reset/else behavior for `ready`).
- Waveform server reads VCD text format only.
- For non-demo usage, restore your original `config/mcp_servers.yaml`.

