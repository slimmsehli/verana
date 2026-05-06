from __future__ import annotations

from config_models import SkillConfig


def compose_skills(skills: list[SkillConfig]) -> dict[str, object]:
    system_parts: list[str] = []
    preferred: list[str] = []
    examples: list[dict[str, str]] = []
    suggested_mode: str | None = None

    for skill in skills:
        if skill.system_prompt:
            system_parts.append(skill.system_prompt.strip())
        for t in skill.preferred_tools:
            if t not in preferred:
                preferred.append(t)
        examples.extend(skill.few_shot_examples)
        if suggested_mode is None and skill.suggested_mode:
            suggested_mode = skill.suggested_mode

    return {
        "system_prompt": "\n\n".join(system_parts),
        "preferred_tools": preferred,
        "few_shot_examples": examples,
        "suggested_mode": suggested_mode,
    }

