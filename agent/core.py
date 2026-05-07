from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent.context import AgentContext
from agent.planner import Planner
from agent.project_context import detect_project_context
from agent.react_loop import ReActLoop
from budget.tracker import BudgetTracker
from config_loader import load_runtime_config
from config_models import ModeConfig
from llm.base import Message
from llm.provider_factory import make_provider
from logging_utils import setup_logging
from mcp.registry import MCPRegistry
from mcp.tool_dispatcher import ToolDispatcher
from modes.registry import ModeRegistry
from plugins.loader import PluginManager
from session.manager import SessionManager
from session.models import BudgetState, SessionMessage
from skills.composer import compose_skills
from skills.registry import SkillRegistry


class Agent:
    def __init__(self, root_dir: Path, env_file: Path | None = None):
        self.root_dir = root_dir
        self.cfg = load_runtime_config(root_dir, env_file=env_file)
        setup_logging(
            log_file=(root_dir / self.cfg.settings.logging.log_file),
            level=self.cfg.settings.logging.level,
        )
        self.skill_registry = SkillRegistry(root_dir)
        self.mode_registry = ModeRegistry(root_dir)
        self.skill_registry.load()
        self.mode_registry.load()
        self.plugin_manager = PluginManager()
        self.plugin_manager.load(
            self.cfg.plugins.plugins,
            plugin_dir=(root_dir / self.cfg.settings.plugins.plugin_dir),
        )

    async def _connect_mcp(self) -> MCPRegistry:
        reg = MCPRegistry()
        await reg.connect_servers(self.cfg.mcp_servers.mcp_servers)
        return reg

    def _resolve_mode(self, mode_name: str) -> ModeConfig:
        return self.mode_registry.get(mode_name)

    async def run_once(
        self,
        user_text: str,
        provider_name: str | None = None,
        model_name: str | None = None,
        mode_name: str | None = None,
        skills: list[str] | None = None,
        session_id: str | None = None,
        title: str = "",
        budget_input: int | None = None,
        budget_output: int | None = None,
        on_event=lambda _k, _v: None,
        tool_approval_callback: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> AgentContext:
        provider_name = provider_name or self.cfg.settings.agent.default_provider
        model_name = model_name or self.cfg.settings.agent.default_model
        mode_name = mode_name or self.cfg.settings.agent.default_mode
        active_skills = list(skills or self.cfg.settings.agent.default_skills)

        mode = self._resolve_mode(mode_name)
        for s in mode.preferred_skills:
            if s not in active_skills:
                active_skills.append(s)
        composed = compose_skills([self.skill_registry.get(s) for s in active_skills if s in self.skill_registry.skills])

        session_mgr = SessionManager(self.root_dir / self.cfg.settings.sessions.storage_dir)
        if session_id:
            metadata = session_mgr.load_metadata(session_id)
            if metadata.provider != provider_name or metadata.model != model_name:
                raise ValueError("Session model is locked; start a new session to change model/provider.")
            messages = session_mgr.load_messages(session_id)
        else:
            budget = BudgetState(
                max_input_tokens=budget_input or self.cfg.settings.budget.max_input_tokens,
                max_output_tokens=budget_output or self.cfg.settings.budget.max_output_tokens,
            )
            metadata = session_mgr.create(
                provider=provider_name,
                model=model_name,
                planner_provider=self.cfg.settings.planner.provider,
                planner_model=self.cfg.settings.planner.model,
                mode=mode.name,
                active_skills=active_skills,
                budget=budget,
                title=title,
            )
            messages = []

        context = AgentContext(
            session_id=metadata.session_id,
            session_dir=session_mgr.session_dir(metadata.session_id),
            provider=provider_name,
            model=model_name,
            mode=mode.name,
            active_skills=active_skills,
            messages=messages,
            metadata=metadata,
        )
        self.plugin_manager.emit("on_session_start", context)

        main_provider = make_provider(provider_name, model_name, self.cfg.providers)
        mcp_registry = await self._connect_mcp()
        dispatcher = ToolDispatcher(mcp_registry, approval_callback=tool_approval_callback)
        budget_tracker = BudgetTracker(
            state=metadata.budget,
            warn_at_percent=self.cfg.settings.budget.warn_at_percent,
            hard_stop=self.cfg.settings.budget.hard_stop,
        )

        if mode.use_planner and self.cfg.settings.planner.enabled:
            plan_provider = make_provider(
                self.cfg.settings.planner.provider,
                self.cfg.settings.planner.model,
                self.cfg.providers,
            )
            planner = Planner(plan_provider, temperature=self.cfg.settings.planner.temperature)
            context.plan = await planner.create_plan(user_text)

        system_prompt = (
            f"You are rtl-agent in {mode.name} mode.\n\n"
            f"Detected project context:\n{detect_project_context(self.root_dir)}\n\n"
            f"{composed.get('system_prompt', '')}\n\n"
            f"{mode.system_prompt_suffix}"
        ).strip()

        context.messages.append(Message(role="user", content=user_text))
        loop = ReActLoop(main_provider, dispatcher, budget_tracker, self.plugin_manager, mode.react_loop)
        answer, full_messages, response = await loop.run_turn(
            messages=context.messages,
            tools=mcp_registry.unified_tools(),
            system_prompt=system_prompt,
            temperature=self.cfg.settings.agent.temperature,
            on_event=on_event,
        )

        context.messages = full_messages + [Message(role="assistant", content=answer, react_step="final")]
        metadata.message_count += 1
        metadata.mode = mode.name
        metadata.active_skills = active_skills
        metadata.budget = budget_tracker.state

        session_mgr.append_message(
            metadata.session_id,
            SessionMessage(
                role="user",
                content=user_text,
                input_tokens=0,
                output_tokens=0,
            ),
        )
        session_mgr.append_message(
            metadata.session_id,
            SessionMessage(
                role="assistant",
                content=answer,
                tool_calls=response.tool_calls,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                react_step="final",
            ),
        )
        session_mgr.save_metadata(metadata.session_id, metadata)

        self.plugin_manager.emit("on_session_end", context)
        await mcp_registry.disconnect_all()
        return context

