"""Trace objects for showing how the skill-based agent made decisions."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTrace:
    user_input: str
    intent: str = "unknown"
    selected_superpower: str = "none"
    tools_used: list[str] = field(default_factory=list)
    memory_updates: list[str] = field(default_factory=list)
    guardrail_result: dict[str, Any] = field(default_factory=dict)
    final_output: str = ""
    router_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_input": self.user_input,
            "intent": self.intent,
            "selected_superpower": self.selected_superpower,
            "tools_used": self.tools_used,
            "memory_updates": self.memory_updates,
            "guardrail_result": self.guardrail_result,
            "router_reason": self.router_reason,
            "final_output": self.final_output,
        }
