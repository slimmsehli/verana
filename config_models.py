from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentSettings(BaseModel):
    name: str = "rtl-agent"
    default_provider: str = "anthropic"
    default_model: str = "claude-sonnet-4-20250514"
    default_mode: str = "debug"
    default_skills: list[str] = Field(default_factory=list)
    max_react_iterations: int = 15
    show_thinking: bool = True
    show_tool_calls: bool = True
    temperature: float = 0.2
    stream_output: bool = True


class PlannerSettings(BaseModel):
    enabled: bool = False
    provider: str = "anthropic"
    model: str = "claude-opus-4-20250514"
    temperature: float = 0.1


class BudgetSettings(BaseModel):
    enabled: bool = True
    max_input_tokens: int = 500_000
    max_output_tokens: int = 100_000
    warn_at_percent: int = 80
    hard_stop: bool = True


class SessionSettings(BaseModel):
    storage_dir: str = "./sessions"
    auto_save: bool = True


class LoggingSettings(BaseModel):
    level: str = "INFO"
    log_file: str = "./logs/agent.log"
    log_react_steps: bool = True


class PluginSettings(BaseModel):
    enabled: bool = True
    plugin_dir: str = "./plugins_user"


class UISettings(BaseModel):
    theme: Literal["dark", "light"] = "dark"
    show_token_count: bool = True
    show_budget_bar: bool = True


class SettingsFile(BaseModel):
    agent: AgentSettings = Field(default_factory=AgentSettings)
    planner: PlannerSettings = Field(default_factory=PlannerSettings)
    budget: BudgetSettings = Field(default_factory=BudgetSettings)
    sessions: SessionSettings = Field(default_factory=SessionSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    ui: UISettings = Field(default_factory=UISettings)


class ProviderConfig(BaseModel):
    api_key: str | None = None
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    base_url: str | None = None
    timeout: int = 120


class OllamaProviderConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    available_models: list[str] = Field(default_factory=list)
    timeout: int = 300


class ProvidersFile(BaseModel):
    providers: dict[str, ProviderConfig | OllamaProviderConfig] = Field(default_factory=dict)


class MCPAuthConfig(BaseModel):
    type: Literal["bearer", "api_key", "oauth"]
    token: str | None = None
    header: str | None = None
    query_param: str | None = None
    value: str | None = None
    token_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] = Field(default_factory=list)


class MCPServerConfig(BaseModel):
    name: str
    description: str = ""
    transport: Literal["stdio", "http"]
    enabled: bool = True
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    auth: MCPAuthConfig | None = None


class MCPServersFile(BaseModel):
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list)


class PluginEntry(BaseModel):
    name: str
    path: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class PluginsFile(BaseModel):
    plugins: list[PluginEntry] = Field(default_factory=list)


class SkillConfig(BaseModel):
    name: str
    version: str = "1.0"
    description: str = ""
    system_prompt: str = ""
    preferred_tools: list[str] = Field(default_factory=list)
    suggested_mode: str | None = None
    few_shot_examples: list[dict[str, str]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ReactLoopModeConfig(BaseModel):
    max_iterations: int = 15
    show_thought: bool = True
    show_action: bool = True
    show_observation: bool = True
    abort_on_error: bool = False
    iteration_warning: int = 10
    output_format: Literal["markdown", "plain", "json"] = "markdown"


class ModeConfig(BaseModel):
    name: str
    description: str = ""
    system_prompt_suffix: str = ""
    preferred_skills: list[str] = Field(default_factory=list)
    use_planner: bool = False
    plan_approval: bool = False
    react_loop: ReactLoopModeConfig = Field(default_factory=ReactLoopModeConfig)


class RuntimeConfig(BaseModel):
    root_dir: Path
    settings: SettingsFile
    providers: ProvidersFile
    mcp_servers: MCPServersFile
    plugins: PluginsFile

