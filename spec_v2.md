# RTL Agent Specification v2 (Production MVP)

Version: 2.0 (MVP Production Profile)  
Status: Draft for Implementation

## 1. Goals

This version defines the minimum features and non-functional requirements needed to operate `rtl-agent` as a production-grade internal platform for engineering teams.

Primary goals:

- Multi-user, auditable, secure agent execution
- Deterministic and recoverable runtime behavior
- Reliable tool orchestration across EDA/MCP systems
- Measurable quality via CI, tests, and SLOs
- Controlled extensibility through plugins and policy

## 2. Scope

Included in v2 MVP:

- Security hardening for credentials, plugins, and tool policies
- Reliability controls (timeouts, retries, circuit breakers)
- Enterprise observability (logs, metrics, traces)
- Production deployment model (containerized service + CLI)
- Demo reference stack with EDA and waveform MCP integrations

Out of scope for MVP:

- Cross-region HA
- Billing/chargeback
- Fine-grained per-token cost optimization
- Advanced multi-agent orchestration

## 3. Production Architecture

Runtime components:

- `Agent Runtime`: ReAct loop, planner, skills/modes, budget enforcement
- `Policy Engine`: validates model/tool/plugin permissions before execution
- `MCP Gateway Layer`: server registry, health checks, auth refresh, failover rules
- `Session Store`: durable local/remote storage for metadata/messages/artifacts
- `Telemetry Layer`: structured logs + metrics + traces

Deployment modes:

- `CLI mode` (single-user local)
- `Service mode` (multi-user via API worker queue)

## 4. Security Requirements

### 4.1 Secrets

- Production must support secret manager backends (Vault/AWS/GCP/Azure).
- `.env` is allowed only for local/dev.
- Secrets must never be logged, exported, or echoed in tool error payloads.

### 4.2 Authentication & Authorization

- Every run is tied to an authenticated user identity.
- Tool execution is policy-gated:
  - allowlist by user/group
  - denylist by tool category
  - environment-aware policies (dev/staging/prod)
- High-risk tools require explicit confirmation with audit trace.

### 4.3 Plugin Trust

- Plugins must be allowlisted and integrity-verified.
- Unsigned/untrusted plugins are rejected in production mode.
- Plugin sandbox mode must be supported for untrusted code paths.

### 4.4 Audit

- Record immutable audit events for:
  - session start/end
  - model selection
  - tool calls and outcomes
  - artifact writes/exports
  - policy denials
- Audit records require timestamp, user, session ID, action, and status.

## 5. Reliability Requirements

### 5.1 LLM Calls

- Retries with exponential backoff and jitter.
- Provider timeout defaults and max timeout caps.
- Circuit breaker per provider after repeated failures.

### 5.2 MCP Calls

- Per-tool timeout and retry policy.
- Server health state: healthy/degraded/down.
- Automatic disable on repeated critical auth/transport failures.
- Clear error propagation as observation text.

### 5.3 Session Durability

- Turn-level atomic writes.
- Crash-safe recovery with no partial turn corruption.
- Resume must preserve model lock and tool chronology.

### 5.4 Budget Safety

- Enforced hard stop behavior in production profiles.
- Optional per-user and per-project budget ceilings.
- Pre-call guardrail: deny request if projected spend exceeds cap.

## 6. Observability Requirements

### 6.1 Logs

- Structured JSON logs with standardized schema:
  - `timestamp`, `level`, `component`, `session_id`, `user_id`, `message`, `extra`
- Secret redaction by default.

### 6.2 Metrics

Expose Prometheus metrics:

- request latency (LLM/tool/planner)
- tool failure rate by server/tool
- token usage by provider/model/user/project
- session success/failure counts
- policy deny counts

### 6.3 Tracing

- OpenTelemetry spans for:
  - ReAct iterations
  - LLM calls
  - tool dispatches
  - plugin hooks

## 7. Quality Gates

Required CI gates:

- lint (`ruff`)
- type-check (`mypy`)
- unit tests (`pytest`)
- integration tests (mock MCP servers)
- packaging/install smoke test (`rtl-agent --help`)
- Python matrix: 3.11, 3.12, 3.13

Release gates:

- zero critical security findings
- all required tests passing
- release notes + migration notes

## 8. Enterprise Operations

- Container image with pinned dependencies and SBOM generation.
- Deployment templates (docker-compose + helm baseline).
- Config profiles: `dev`, `staging`, `prod`.
- Runbook for incident response and rollback.
- SLOs:
  - Session start success >= 99%
  - Tool dispatch success >= 97% (excluding user/tool errors)
  - P95 response latency target per provider

## 9. API & CLI Compatibility

- Semantic versioning for CLI/API behaviors.
- Backward-compatible config migration tooling.
- Deprecation policy with warning period and migration docs.

## 10. Demo Acceptance Requirements

The MVP must include a demonstrator that proves:

- A simple MCP server can be connected and called.
- EDA tools (`verilator`, `yosys`) can be orchestrated via MCP.
- A custom waveform MCP server can parse/query VCD.
- Agent can run compile/lint, detect failure, and provide debug guidance.
- Verification artifacts are generated and stored in session artifacts.

## 11. Milestone Plan

M1: Hardening Foundation

- policy engine, retry/timeout framework, audit schema

M2: Observability + Deployment

- metrics, traces, containerization, environment profiles

M3: Domain Demo

- demo MCP stack + buggy RTL testcase + scripted walkthrough

M4: Production Readiness Review

- security review, performance baseline, release checklist sign-off

