"""RoomiePeace skill-based agent orchestration."""

from __future__ import annotations

from typing import Any

from .guardrails import guardrail_check
from .memory import MemoryStore
from .router import route
from .superpowers import (
    chore_planner,
    conflict_mediator,
    karma_report,
    line_announcement,
    receipt_splitter,
    roomie_court,
)
from .tools.text_tools import extract_constraints, extract_roommates, join_names
from .trace import AgentTrace


class RoomiePeaceAgent:
    def __init__(self, memory: MemoryStore | None = None) -> None:
        self.memory = memory or MemoryStore()

    def handle(self, user_input: str) -> dict[str, Any]:
        user_input = user_input.strip()
        if not user_input:
            user_input = "請產生本週 Karma 排行榜"

        privacy_guard = guardrail_check(user_input)
        if "requests_private_debt_or_identity_info" in privacy_guard["issues"]:
            result = self._guardrail_response(user_input, privacy_guard)
            return result
        if "requests_real_money_movement" in privacy_guard["issues"]:
            result = self._guardrail_response(user_input, privacy_guard)
            return result

        route_result = route(user_input)
        trace = AgentTrace(
            user_input=user_input,
            intent=route_result.intent,
            selected_superpower=route_result.selected_superpower,
            router_reason=route_result.reason,
        )

        if route_result.intent == "setup_roommates":
            result = self._setup_roommates(user_input)
        elif route_result.intent == "receipt_splitter":
            result = receipt_splitter.handle(user_input, self.memory)
        elif route_result.intent == "chore_planner":
            result = chore_planner.handle(user_input, self.memory)
        elif route_result.intent == "conflict_mediator":
            result = conflict_mediator.handle(user_input, self.memory)
        elif route_result.intent == "roomie_court":
            result = roomie_court.handle(user_input, self.memory)
        elif route_result.intent == "karma_report":
            result = karma_report.handle(user_input, self.memory)
        elif route_result.intent == "line_announcement":
            result = line_announcement.handle(user_input, self.memory)
        else:
            result = karma_report.handle(user_input, self.memory)

        guardrail_result = guardrail_check(
            f"{result.get('response_markdown', '')}\n{result.get('line_message', '')}"
        )
        if not guardrail_result["safe"]:
            result["response_markdown"] = (
                "### Guardrail 已介入\n\n"
                f"{guardrail_result['suggestion']}\n\n"
                "我已將輸出降級為中性提醒，避免羞辱、歧視或隱私外洩。"
            )
            result["line_message"] = guardrail_result["suggestion"]

        trace.tools_used = result.get("tools_used", [])
        trace.memory_updates = result.get("memory_updates", [])
        trace.guardrail_result = guardrail_result
        trace.final_output = result.get("response_markdown", "")
        result["trace"] = trace.to_dict()
        result["memory_snapshot"] = self.memory.snapshot()
        return result

    def _setup_roommates(self, user_input: str) -> dict[str, Any]:
        snapshot = self.memory.snapshot()
        roommates = extract_roommates(user_input, snapshot["roommates"])
        self.memory.set_roommates(roommates)
        constraints = extract_constraints(user_input, roommates)
        for roommate, constraint in constraints.items():
            self.memory.update_constraint(roommate, constraint)
        event = self.memory.add_event(
            "roommate_setup_updated",
            "system",
            {"roommates": roommates, "constraints": constraints},
        )
        constraint_lines = [
            f"- {roommate}：{self.memory.snapshot()['constraints'].get(roommate, '無特殊限制')}"
            for roommate in roommates
        ]
        line_message = (
            f"RoomiePeace 已建立室友資料：{join_names(roommates)}。\n"
            "本週限制已更新，後續分帳、家事與提醒都會使用這份 memory。"
        )
        markdown = f"""
### roommate-setup：建立室友資料

已建立室友名單：**{join_names(roommates)}**

**本週狀態**
{chr(10).join(constraint_lines)}

接下來可以直接跑分帳、家事排班、衝突調解或室友法庭。
""".strip()
        return {
            "intent": "setup_roommates",
            "skill": "roommate-setup",
            "response_markdown": markdown,
            "line_message": line_message,
            "tables": {
                "室友狀態": [
                    {"室友": roommate, "狀態": self.memory.snapshot()["constraints"].get(roommate, "無特殊限制")}
                    for roommate in roommates
                ]
            },
            "tools_used": ["extract_roommates", "extract_constraints", "MemoryStore.set_roommates"],
            "memory_updates": [f"roommate_setup_updated event @ {event['timestamp']}"],
        }

    def _guardrail_response(self, user_input: str, guardrail_result: dict[str, Any]) -> dict[str, Any]:
        trace = AgentTrace(
            user_input=user_input,
            intent="guardrail",
            selected_superpower="guardrail",
            tools_used=["guardrail_check"],
            memory_updates=[],
            guardrail_result=guardrail_result,
            final_output=guardrail_result["suggestion"],
            router_reason="guardrail pre-check",
        )
        markdown = f"""
### Guardrail 已攔截

這個要求可能涉及私人欠款資料、真實金流或不必要的個資揭露。

{guardrail_result['suggestion']}

可以改成：「請提供匿名分帳摘要」或「請產生不點名的群組提醒」。
""".strip()
        return {
            "intent": "guardrail",
            "skill": "guardrail",
            "response_markdown": markdown,
            "line_message": guardrail_result["suggestion"],
            "tables": {},
            "tools_used": ["guardrail_check"],
            "memory_updates": [],
            "trace": trace.to_dict(),
            "memory_snapshot": self.memory.snapshot(),
        }
