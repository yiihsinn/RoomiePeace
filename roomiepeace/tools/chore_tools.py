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
            tasks.append(default_task)
    return tasks or DEFAULT_TASKS.copy()


def _has_constraint(name: str, constraints: dict[str, str], keyword: str) -> bool:
    return keyword in constraints.get(name, "")


def _previous_loads(roommates: list[str], chore_history: list[dict[str, Any]]) -> dict[str, int]:
    loads = {name: 0 for name in roommates}
    for schedule in chore_history[-3:]:
        for assignment in schedule.get("assignments", []):
            assignee = assignment.get("assignee")
            if assignee in loads:
                loads[assignee] += int(assignment.get("difficulty", 1))
    return loads


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
    loads = _previous_loads(roommates, chore_history)
    assignments: list[dict[str, Any]] = []

    exam_people = {name for name in roommates if _has_constraint(name, constraints, "期中考") or f"{name}這週期中考" in text}
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
            assignee = sorted(trash_debtors, key=lambda person: roommates.index(person))[0]
            reason = "近期垃圾任務有延宕，這週補回"
        elif name == "補衛生紙" and exam_people:
            assignee = sorted(exam_people, key=lambda person: roommates.index(person))[0]
            reason = "考試週安排較輕任務"
        elif name == "拖地" and "阿明" in roommates:
            assignee = "阿明"
            reason = "可避開週三晚上不在的限制"
        elif difficulty >= 3:
            assignee = _least_loaded(loads, avoid=exam_people, preferred=roommates)
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

    fairness_score = calculate_fairness_score(assignments, constraints)
    commentary = build_chore_commentary(assignments, constraints)
    return {
        "assignments": assignments,
        "fairness_score": fairness_score,
        "loads": loads,
        "commentary": commentary,
    }


def calculate_fairness_score(assignments: list[dict[str, Any]], constraints: dict[str, str]) -> int:
    loads: dict[str, int] = {}
    for assignment in assignments:
        loads[assignment["assignee"]] = loads.get(assignment["assignee"], 0) + int(assignment["difficulty"])
    if not loads:
        return 100
    values = list(loads.values())
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    spread_penalty = int(math.sqrt(variance) * 7)
    range_penalty = (max(values) - min(values)) * 3
    constraint_penalty = sum(
        3
        for constraint in constraints.values()
        if any(keyword in constraint for keyword in ["期中考", "不在", "忘記"])
    )
    return max(60, min(100, 100 - spread_penalty - range_penalty - constraint_penalty))


def build_chore_commentary(assignments: list[dict[str, Any]], constraints: dict[str, str]) -> list[str]:
    comments = []
    for name, constraint in constraints.items():
        if "期中考" in constraint:
            comments.append(f"{name}因考試週受到保護。")
        if "忘記倒垃圾" in constraint:
            comments.append(f"{name}因垃圾任務延宕，本週重新進入社會服務流程。")
    if not comments:
        comments.append("本週排班以 difficulty 分數平均分配。")
    return comments
