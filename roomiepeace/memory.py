"""Event-based memory for the RoomiePeace prototype."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_PATH = PROJECT_ROOT / "data" / "memory.json"


SEED_MEMORY: dict[str, Any] = {
    "roommates": ["阿明", "小美", "冠宇", "庭萱"],
    "constraints": {
        "小美": "本週期中考",
        "阿明": "週三晚上不在",
        "冠宇": "常常忘記倒垃圾",
        "庭萱": "無特殊限制",
    },
    "inventory": {
        "衛生紙": "剩1包",
        "垃圾袋": "已用完",
        "洗衣精": "剩30%",
    },
    "expenses": [],
    "chores": [],
    "court_cases": [],
    "events": [],
    "karma": {
        "阿明": 80,
        "小美": 76,
        "冠宇": 43,
        "庭萱": 88,
    },
}


class MemoryStore:
    """Small JSON-backed memory store.

    The app intentionally uses event-based memory instead of plain chat logs so
    the demo can show which life events changed the agent state.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_MEMORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_or_seed()

    def _load_or_seed(self) -> dict[str, Any]:
        if not self.path.exists():
            data = deepcopy(SEED_MEMORY)
            self._write(data)
            return data

        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        merged = deepcopy(SEED_MEMORY)
        merged.update(data)
        for key in ["constraints", "inventory", "karma"]:
            merged[key] = {**SEED_MEMORY[key], **data.get(key, {})}
        for key in ["expenses", "chores", "court_cases", "events"]:
            merged[key] = data.get(key, [])
        self._write(merged)
        return merged

    def _write(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def save(self) -> None:
        self._write(self.data)

    def reset(self) -> None:
        self.data = deepcopy(SEED_MEMORY)
        self.save()

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self.data)

    def now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def add_event(self, event_type: str, actor: str, data: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_type": event_type,
            "timestamp": self.now(),
            "actor": actor,
            "data": data,
        }
        self.data.setdefault("events", []).append(event)
        self.save()
        return event

    def set_roommates(self, roommates: list[str]) -> None:
        self.data["roommates"] = roommates
        self.data["constraints"] = {
            name: self.data.get("constraints", {}).get(name, "無特殊限制")
            for name in roommates
        }
        self.data["karma"] = {
            name: self.data.get("karma", {}).get(name, 70)
            for name in roommates
        }
        self.save()

    def update_constraint(self, roommate: str, constraint: str) -> None:
        self.data.setdefault("constraints", {})[roommate] = constraint or "無特殊限制"
        self.save()

    def update_inventory(self, item: str, status: str) -> None:
        self.data.setdefault("inventory", {})[item] = status
        self.save()

    def bump_karma(self, roommate: str, delta: int) -> None:
        karma = self.data.setdefault("karma", {})
        karma[roommate] = max(0, min(100, int(karma.get(roommate, 70) + delta)))
        self.save()

    def set_karma(self, scores: dict[str, int]) -> None:
        self.data["karma"] = {name: int(score) for name, score in scores.items()}
        self.save()

    def record_expense(self, expense: dict[str, Any]) -> dict[str, Any]:
        self.data.setdefault("expenses", []).append(expense)
        event = self.add_event(
            "expense_created",
            expense["payer"],
            {
                "items": [item["name"] for item in expense["shared_items"]],
                "shared_total": expense["shared_total"],
                "split_members": expense["split_members"],
                "transfers": expense["transfers"],
            },
        )
        self.bump_karma(expense["payer"], 2)
        for item in expense["shared_items"]:
            self.update_inventory(item["name"], "剛補貨")
        return event

    def record_chore_assignments(
        self,
        assignments: list[dict[str, Any]],
        fairness_score: int,
    ) -> list[dict[str, Any]]:
        schedule = {
            "timestamp": self.now(),
            "fairness_score": fairness_score,
            "assignments": assignments,
        }
        self.data.setdefault("chores", []).append(schedule)
        events = []
        for assignment in assignments:
            event = self.add_event(
                "chore_assigned",
                "system",
                {
                    "chore": assignment["task"],
                    "assigned_to": assignment["assignee"],
                    "difficulty": assignment["difficulty"],
                    "reason": assignment["reason"],
                },
            )
            events.append(event)
            self.bump_karma(assignment["assignee"], assignment["difficulty"])
        return events

    def record_conflict(self, target: str, topic: str, risk: int) -> dict[str, Any]:
        event = self.add_event(
            "conflict_mediated",
            "system",
            {"target": target, "topic": topic, "tone_risk": risk},
        )
        if target:
            self.bump_karma(target, -1)
        return event

    def record_court_case(self, case: dict[str, Any]) -> dict[str, Any]:
        self.data.setdefault("court_cases", []).append(case)
        event = self.add_event(
            "court_case_created",
            "system",
            {
                "case_name": case["case_name"],
                "defendant": case["defendant"],
                "verdict": case["verdict"],
            },
        )
        if case.get("defendant"):
            self.bump_karma(case["defendant"], -3)
        return event

    def record_announcement(self, title: str) -> dict[str, Any]:
        return self.add_event("line_announcement_created", "system", {"title": title})
