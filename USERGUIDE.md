# rtl-agent User Guide

This guide explains how to use all major features of `rtl-agent` from setup to day-to-day workflows.

## 1) What rtl-agent does

`rtl-agent` is a CLI AI assistant for RTL debug and verification workflows. It provides:

- Multi-provider LLM backend support (`anthropic`, `openai`, `gemini`, `ollama`)
- MCP tool orchestration (`stdio` and `http` transports)
- Composable skills (task-focused instruction packs)
- Modes (high-level behavior profiles like `debug`, `verify`, `review`)
- ReAct loop execution (Thought -> Action -> Observation)
- Session persistence and resume
- Token budget tracking and enforcement
- Plugin hooks and auto-discovery

---

## 2) Project layout

Important locations:

- `config/` — editable runtime YAML config
- `skills/builtin/` and `config/skills/` — built-in and user skills
- `modes/builtin/` and `config/modes/` — built-in and user modes
- `plugins_user/` — drop-in plugin Python files
- `sessions/` — saved sessions (messages, metadata, artifacts)
- `logs/agent.log` — structured JSON logs

---

## 3) Setup

## 3.1 Python environment

```bash
module load python/3.13.0
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3.2 Configure secrets

```bash
cp .env.example .env
```

Fill in keys in `.env`:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- MCP/plugin-related keys (if needed)

## 3.3 Validate project compiles

```bash
python -m compileall .
```

---

## 4) Configuration files

Core config files:

- `config/settings.yaml`
- `config/providers.yaml`
- `config/mcp_servers.yaml`
- `config/plugins.yaml`

Env var interpolation is supported with `${VAR_NAME}` syntax.

Examples:

- Provider/model defaults in `config/settings.yaml`
- API keys/models in `config/providers.yaml`
- MCP servers and auth in `config/mcp_servers.yaml`
- Plugin registration in `config/plugins.yaml`

---

## 5) Basic commands

Show command help:

```bash
rtl-agent --help
```

Top-level command groups:

- `run`
- `session`
- `skill`
- `mode`
- `mcp`
- `plugin`
- `budget`
- `config`
- `model`

---

## 6) Running the agent

Start interactive loop:

```bash
rtl-agent run
```

Common overrides:

```bash
rtl-agent run \
  --provider anthropic \
  --model claude-sonnet-4-20250514 \
  --mode debug \
  --skills rtl_debug,waveform_analyzer \
  --title "debug x-prop on ready"
```

Resume existing session:

```bash
rtl-agent run --session <session-id>
```

Budget override per run:

```bash
rtl-agent run --budget-input 200000 --budget-output 50000
```

Use additional env file:

```bash
rtl-agent run --env-file ./my.env
```

---

## 7) In-session slash commands

Available inside `rtl-agent run`:

- `/help` — show slash commands
- `/mode <name>` — change mode for next turn
- `/skill add <name>` — activate a skill
- `/skill remove <name>` — deactivate a skill
- `/skill list` — list active skills
- `/plan` — switch next turn to planner-focused mode
- `/tools` — list currently available MCP tools
- `/budget` — show current budget usage
- `/history` — show message/token totals
- `/save` — confirm session persistence
- `/export` — export session markdown into `artifacts/`
- `/clear` — clear active context (start new session on next prompt)
- `/quit` — exit loop

---

## 8) Sessions and history

List sessions:

```bash
rtl-agent session list
rtl-agent session list --filter "x-prop"
```

Show metadata:

```bash
rtl-agent session show <session-id>
```

Export session:

```bash
rtl-agent session export <session-id> --format md
rtl-agent session export <session-id> --format html
rtl-agent session export <session-id> --format json
```

Tag session:

```bash
rtl-agent session tag <session-id> --add critical
```

List artifacts:

```bash
rtl-agent session artifacts <session-id>
```

Delete session:

```bash
rtl-agent session delete <session-id>
```

Session files are stored under:

`sessions/<session-id>/`

- `metadata.json`
- `messages.jsonl`
- `artifacts/`

---

## 9) Skills

List all skills (built-in + user):

```bash
rtl-agent skill list
```

Inspect skill:

```bash
rtl-agent skill show rtl_debug
```

Create/edit/delete user skill:

```bash
rtl-agent skill create my_skill
rtl-agent skill edit my_skill
rtl-agent skill delete my_skill
```

Skill composition behavior:

- `system_prompt`: concatenated in activation order
- `preferred_tools`: union, deduplicated
- `few_shot_examples`: concatenated in activation order
- `suggested_mode`: first active suggestion wins

---

## 10) Modes

Built-in modes:

- `debug`
- `plan`
- `code`
- `spec`
- `verify`
- `review`

Commands:

```bash
rtl-agent mode list
rtl-agent mode show debug
rtl-agent mode create my_mode
rtl-agent mode edit my_mode
```

Modes control:

- System prompt suffix
- Preferred skills
- Planner usage
- ReAct loop parameters

---

## 11) MCP servers and tools

List configured servers:

```bash
rtl-agent mcp list
```

Health check:

```bash
rtl-agent mcp status
```

List tools from one server:

```bash
rtl-agent mcp tools waveform-tools
```

Enable/disable/reload:

```bash
rtl-agent mcp enable <name>
rtl-agent mcp disable <name>
rtl-agent mcp reload
```

Add/remove server:

```bash
rtl-agent mcp add
rtl-agent mcp remove <name>
```

Tool names are namespaced:

`<server-name>__<tool-name>`

Auth supported in `config/mcp_servers.yaml`:

- `bearer`
- `api_key` (header or query param)
- `oauth` (client credentials, auto-refresh token)

---

## 12) Plugins

List and inspect plugins:

```bash
rtl-agent plugin list
rtl-agent plugin show vcd_preprocessor
```

Enable/disable/reload:

```bash
rtl-agent plugin enable <name>
rtl-agent plugin disable <name>
rtl-agent plugin reload
```

Plugin sources:

- Explicit registration via `config/plugins.yaml`
- Auto-discovery of `*.py` in `plugins_user/`

Plugin hooks include:

- Session start/end
- Before/after LLM call
- Before/after tool call
- Final answer
- Budget warning/exhaustion

---

## 13) Budget controls

Show last session budget:

```bash
rtl-agent budget status
```

Set default budget caps:

```bash
rtl-agent budget set --input 300000 --output 80000
```

Live budget info appears after each assistant turn.

---

## 14) Config CLI

Show merged config:

```bash
rtl-agent config show
```

Validate config:

```bash
rtl-agent config validate
```

Get/set setting:

```bash
rtl-agent config get agent.default_mode
rtl-agent config set agent.default_mode verify
```

Open settings in editor:

```bash
rtl-agent config edit
```

---

## 15) Models

List models from all providers:

```bash
rtl-agent model list
```

List by provider:

```bash
rtl-agent model list --provider anthropic
```

Set default provider/model:

```bash
rtl-agent model set anthropic/claude-sonnet-4-20250514
```

---

## 16) Typical workflows

## 16.1 RTL simulation failure debug

```bash
rtl-agent run --mode debug --skills rtl_debug,waveform_analyzer
```

Inside session:

- Ask for root-cause analysis with waveform/log paths
- Use `/tools` to inspect available MCP tool surface
- Use `/budget` to monitor long investigations

## 16.2 Verification plan generation

```bash
rtl-agent run --mode verify --skills verification_plan
```

Then export:

```bash
rtl-agent session export <session-id> --format md
```

## 16.3 RTL review pass

```bash
rtl-agent run --mode review --skills lint_checker
```

---

## 17) Logging and troubleshooting

Logs are written as JSON lines to:

`logs/agent.log`

Common checks:

- `rtl-agent config validate`
- `rtl-agent mcp status`
- `rtl-agent plugin reload`
- `python -m compileall .`

If an MCP server fails at startup, agent continues without that server’s tools.

---

## 18) Notes and best practices

- Keep `.env` out of version control.
- Start with built-in `debug` mode and add skills as needed.
- Use session tags to organize critical investigations.
- Use planner-enabled modes for multi-step tasks.
- Export sessions into `artifacts/` for sharing/review.

