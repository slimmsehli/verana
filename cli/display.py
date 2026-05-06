from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

console = Console()


def show_thought(text: str) -> None:
    console.print(f"[dim][Thought][/dim] {text}")


def show_action(text: str) -> None:
    console.print(f"[cyan][Action -> {text}][/cyan]")


def show_observation(text: str) -> None:
    console.print(f"[yellow][Observation][/yellow] {text}")


def show_warning(text: str) -> None:
    console.print(f"[yellow][Warning][/yellow] {text}")


def show_error(text: str) -> None:
    console.print(f"[red][Error][/red] {text}")


def show_final(text: str) -> None:
    console.print(Panel.fit(text, title="rtl-agent", border_style="white"))


def budget_line(used_in: int, max_in: int, used_out: int, max_out: int) -> str:
    pct_in = (used_in / max_in) if max_in else 0
    pct_out = (used_out / max_out) if max_out else 0
    pct = max(pct_in, pct_out)
    bars = int(pct * 10)
    bar = "▓" * bars + "░" * (10 - bars)
    return f"[Budget {bar} {int(pct*100)}% in: {used_in}/{max_in} out: {used_out}/{max_out}]"

