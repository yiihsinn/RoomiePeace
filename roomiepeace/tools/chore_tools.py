"""Chore planning tools."""

from __future__ import annotations

import math
from typing import Any


DEFAULT_TASKS = [
    {"task": "倒垃圾", "difficulty": 1},
    {"task": "補衛生紙", "difficulty": 1},
    {"task": "拖地", "difficulty": 2},
    {"task": "洗浴室", "difficulty": 3},
]


def parse_chore_tasks(text: str) -> list[dict[str, Any]]:
    tasks = []
    for default_task in DEFAULT_TASKS:
        if default_task["task"] in text:
            tasks.append(default_task.copy())
    return tasks or [task.copy() for task in DEFAULT_TASKS]


def _has_constraint(name: str, constraints: dict[str, str], keyword: str) -> bool:
    return keyword in constraints.get(name, "")


def calculate_recent_chore_loads(roommates: list[str], chore_history: list[dict[str, Any]]) -> dict[str, int]:
    loads = {name: 0 for name in roommates}
    for schedule in chore_history[-3:]:
        for assignment in schedule.get("assignments", []):
            assignee = assignment.get("assignee")
            if assignee in loads:
                loads[assignee] += int(assignment.get("difficulty", 1))
    return loads


def _ordered_members(names: set[str], roommates: list[str]) -> list[str]:
    return [name for name in roommates if name in names]


def _least_loaded(
    loads: dict[str, int],
    avoid: set[str] | None = None,
    preferred: list[str] | None = None,
) -> str:
    avoid = avoid or set()
    preferred = preferred or list(loads)
    candidates = [name for name in preferred if name in loads and name not in avoid]
    if not candidates:
        candidates = [name for name in loads if name not in avoid] or list(loads)
    if not candidates:
        raise ValueError("at least one roommate is required to assign chores")
    return min(candidates, key=lambda name: (loads[name], preferred.index(name) if name in preferred else 99))


def generate_chore_schedule(
    text: str,
    roommates: list[str],
    constraints: dict[str, str],
    chore_history: list[dict[str, Any]],
) -> dict[str, Any]:
    tasks = parse_chore_tasks(text)
    task_by_name = {task["task"]: task for task in tasks}
    ordered_names = [task for task in ["倒垃圾", "拖地", "洗浴室", "補衛生紙"] if task in task_by_name]
    ordered_tasks = [task_by_name[name] for name in ordered_names]
    previous_loads = calculate_recent_chore_loads(roommates, chore_history)
    loads = previous_loads.copy()
    assignments: list[dict[str, Any]] = []

    if not roommates:
        return {
            "assignments": [],
            "fairness_score": 100,
            "previous_loads": {},
            "loads": {},
            "commentary": ["目前沒有室友資料，請先建立室友名單。"],
        }

    exam_people = {
        name
        for name in roommates
        if _has_constraint(name, constraints, "期中考")
        or _has_constraint(name, constraints, "考試")
        or f"{name}這週期中考" in text
    }
    away_people = {
        name
        for name in roommates
        if _has_constraint(name, constraints, "不在") or f"{name}不在" in text
    }
    trash_debtors = {
        name
        for name in roommates
        if _has_constraint(name, constraints, "忘記倒垃圾")
        or f"{name}上週沒倒垃圾" in text
        or f"{name}又忘記倒垃圾" in text
    }

    for task in ordered_tasks:
        name = task["task"]
        difficulty = int(task["difficulty"])
        reason = "依據近期負擔平均分配"

        if name == "倒垃圾" and trash_debtors:
            assignee = _least_loaded(loads, preferred=_ordered_members(trash_debtors, roommates))
            reason = "近期垃圾任務有延宕，這週補回"
        elif name == "補衛生紙" and exam_people:
            assignee = _least_loaded(loads, preferred=_ordered_members(exam_people, roommates))
            reason = "考試週安排較輕任務"
        elif name == "倒垃圾":
            assignee = _least_loaded(loads, avoid=away_people, preferred=roommates)
            if away_people:
                reason = "倒垃圾需要準時處理，避開本週不在的室友"
        elif difficulty >= 2:
            assignee = _least_loaded(loads, avoid=exam_people, preferred=roommates)
            if exam_people:
                reason = "考試週避開較重任務，並依近期負擔分配"
            elif difficulty >= 3:
                reason = "本週負擔較低，適合承接較重任務"
        else:
            assignee = _least_loaded(loads, preferred=roommates)

        assignments.append(
            {
                "task": name,
                "assignee": assignee,
                "difficulty": difficulty,
                "reason": reason,
            }
        )
        loads[assignee] = loads.get(assignee, 0) + difficulty

    fairness_score = calculate_fairness_score(assignments, roommates, previous_loads)
    commentary = build_chore_commentary(assignments, constraints, previous_loads)
    return {
        "assignments": assignments,
        "fairness_score": fairness_score,
        "previous_loads": previous_loads,
        "loads": loads,
        "commentary": commentary,
    }


def calculate_fairness_score(
    assignments: list[dict[str, Any]],
    roommates: list[str] | None = None,
    previous_loads: dict[str, int] | None = None,
) -> int:
    previous_loads = previous_loads or {}
    members = list(dict.fromkeys(roommates or list(previous_loads)))
    for assignment in assignments:
        assignee = assignment["assignee"]
        if assignee not in members:
            members.append(assignee)

    loads = {name: int(previous_loads.get(name, 0)) for name in members}
    for assignment in assignments:
        loads[assignment["assignee"]] = loads.get(assignment["assignee"], 0) + int(assignment["difficulty"])
    if not loads:
        return 100

    values = list(loads.values())
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    spread_penalty = int(math.sqrt(variance) * 8)
    range_penalty = (max(values) - min(values)) * 4
    return max(0, min(100, 100 - spread_penalty - range_penalty))


def build_chore_commentary(
    assignments: list[dict[str, Any]],
    constraints: dict[str, str],
    previous_loads: dict[str, int] | None = None,
) -> list[str]:
    comments = []
    for name, constraint in constraints.items():
        if "期中考" in constraint:
            comments.append(f"{name}因考試週受到保護。")
        if "忘記倒垃圾" in constraint:
            comments.append(f"{name}因垃圾任務延宕，本週重新進入社會服務流程。")
    if previous_loads and any(previous_loads.values()):
        comments.append("本週排班已納入最近三次排班的 difficulty 負擔。")
    if not comments:
        comments.append("本週排班以 difficulty 分數平均分配。")
    return comments
