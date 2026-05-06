# rtl-agent

`rtl-agent` is a Python 3.11+ CLI AI agent for RTL debug and verification workflows.

## Implemented Features

- Unified LLM provider layer (`anthropic`, `openai`, `gemini`, `ollama`)
- MCP integration over `stdio` and `http` with auth strategies:
  - bearer token
  - API key (header or query param)
  - OAuth2 client credentials with in-memory token refresh
- Skill registry and composition (built-in + user-defined YAML)
- Mode registry (built-in + user-defined YAML)
- ReAct loop (Thought -> Action -> Observation) with iteration controls
- Optional planner pass using separately configured planner model
- Session persistence (`metadata.json`, `messages.jsonl`, `artifacts/`)
- Token budget tracker with warning/exhaustion hooks
- Plugin system with hook lifecycle and auto-discovery
- Typer CLI command groups:
  - `run`, `session`, `skill`, `mode`, `mcp`, `plugin`, `budget`, `config`, `model`

## Quick Start

```bash
sudo apt update
sudo apt upgrade
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13
sudo apt install python3.13-venv python3.13-dev
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
rtl-agent run
```

## Config Files

Configuration is loaded from:

- `config/settings.yaml`
- `config/providers.yaml`
- `config/mcp_servers.yaml`
- `config/plugins.yaml`
- `config/skills/*.yaml`
- `config/modes/*.yaml`

Environment variable interpolation is supported with `${VAR_NAME}` syntax.

