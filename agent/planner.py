from __future__ import annotations

from llm.base import LLMProvider, Message


class Planner:
    def __init__(self, provider: LLMProvider, temperature: float = 0.1):
        self.provider = provider
        self.temperature = temperature

    async def create_plan(self, user_request: str, context_summary: str = "") -> list[str]:
        prompt = (
            "Create a concise numbered execution plan for this RTL task. "
            "Return only numbered lines.\n\n"
            f"Context:\n{context_summary}\n\nTask:\n{user_request}"
        )
        response = await self.provider.complete(
            messages=[Message(role="user", content=prompt)],
            tools=[],
            system="You are a planning assistant for RTL debug and verification.",
            temperature=self.temperature,
            stream=False,
        )
        lines = [line.strip() for line in response.content.splitlines() if line.strip()]
        normalized: list[str] = []
        for line in lines:
            if line[0].isdigit():
                normalized.append(line)
        return normalized or ["1. Analyze the request.", "2. Execute relevant tools.", "3. Produce final answer."]

