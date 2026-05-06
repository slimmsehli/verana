from __future__ import annotations

from dataclasses import dataclass

from session.models import BudgetState


@dataclass
class BudgetStatus:
    used_input_tokens: int
    max_input_tokens: int
    used_output_tokens: int
    max_output_tokens: int
    percent: float
    warning: bool
    exhausted: bool


class BudgetTracker:
    def __init__(self, state: BudgetState, warn_at_percent: int = 80, hard_stop: bool = True):
        self.state = state
        self.warn_at_percent = warn_at_percent
        self.hard_stop = hard_stop
        self._warned = False

    def add_usage(self, input_tokens: int, output_tokens: int) -> BudgetStatus:
        self.state.used_input_tokens += max(0, input_tokens)
        self.state.used_output_tokens += max(0, output_tokens)
        return self.status()

    def status(self) -> BudgetStatus:
        pct = self.state.consumed_pct()
        warning = pct >= self.warn_at_percent
        exhausted = (
            self.state.used_input_tokens >= self.state.max_input_tokens
            or self.state.used_output_tokens >= self.state.max_output_tokens
        )
        return BudgetStatus(
            used_input_tokens=self.state.used_input_tokens,
            max_input_tokens=self.state.max_input_tokens,
            used_output_tokens=self.state.used_output_tokens,
            max_output_tokens=self.state.max_output_tokens,
            percent=pct,
            warning=warning,
            exhausted=exhausted,
        )

    def should_emit_warning(self) -> bool:
        st = self.status()
        if st.warning and not self._warned:
            self._warned = True
            return True
        return False

