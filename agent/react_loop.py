from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from budget.tracker import BudgetTracker
from config_models import ReactLoopModeConfig
from llm.base import LLMProvider, LLMResponse, Message
from mcp.tool_dispatcher import ToolDispatcher
from plugins.loader import PluginManager

logger = logging.getLogger(__name__)


class ReActLoop:
    def __init__(
        self,
        llm: LLMProvider,
        dispatcher: ToolDispatcher,
        budget: BudgetTracker,
        plugins: PluginManager,
        loop_cfg: ReactLoopModeConfig,
    ):
        self.llm = llm
        self.dispatcher = dispatcher
        self.budget = budget
        self.plugins = plugins
        self.loop_cfg = loop_cfg

    async def _llm_with_retry(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system_prompt: str,
        temperature: float,
        stream: bool,
    ) -> LLMResponse:
        delay = 1
        for attempt in range(1, 4):
            try:
                return await self.llm.complete(messages, tools, system_prompt, temperature, stream)
            except Exception:
                if attempt >= 3:
                    raise
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
        raise RuntimeError("unreachable")

    async def run_turn(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        system_prompt: str,
        temperature: float,
        on_event,
    ) -> tuple[str, list[Message], LLMResponse]:
        latest_response: LLMResponse | None = None
        for idx in range(self.loop_cfg.max_iterations):
            self.plugins.emit("on_before_llm_call", messages, tools)
            response = await self._llm_with_retry(messages, tools, system_prompt, temperature, stream=False)
            self.plugins.emit("on_after_llm_call", response)
            latest_response = response

            status = self.budget.add_usage(response.input_tokens, response.output_tokens)
            if self.budget.should_emit_warning():
                self.plugins.emit("on_budget_warning", status.__dict__)

            if self.loop_cfg.show_thought and response.content:
                on_event("thought", response.content[:300])

            if response.stop_reason == "end_turn" or not response.tool_calls:
                self.plugins.emit("on_final_answer", response.content)
                on_event("final", response.content)
                if status.exhausted and self.budget.hard_stop:
                    self.plugins.emit("on_budget_exhausted", status.__dict__)
                return response.content, messages, response

            if self.loop_cfg.show_action:
                for tc in response.tool_calls:
                    on_event("action", tc["function"]["name"])

            tool_results: list[dict[str, Any]] = []
            for tc in response.tool_calls:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                self.plugins.emit("on_before_tool_call", name, args)
                try:
                    result = await self.dispatcher.dispatch(name, args)
                except Exception as exc:
                    if self.loop_cfg.abort_on_error:
                        raise
                    result = {"error": str(exc)}
                self.plugins.emit("on_after_tool_call", name, args, result)
                tool_results.append({"tool_call_id": tc["id"], "name": name, "result": result})
                if self.loop_cfg.show_observation:
                    on_event("observation", f"{name}: {str(result)[:300]}")

            messages.append(
                Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                    react_step="action",
                )
            )
            for tr in tool_results:
                messages.append(
                    Message(
                        role="tool",
                        content=json.dumps(tr["result"]),
                        tool_call_id=tr["tool_call_id"],
                        react_step="observation",
                    )
                )

            if status.exhausted and self.budget.hard_stop:
                self.plugins.emit("on_budget_exhausted", status.__dict__)
                return "Budget exhausted.", messages, response

            remaining = self.loop_cfg.max_iterations - idx - 1
            if remaining <= self.loop_cfg.iteration_warning:
                on_event("warning", f"{remaining} ReAct iterations left.")

        return "Iteration limit reached.", messages, latest_response or LLMResponse("", [], 0, 0, "end_turn")

