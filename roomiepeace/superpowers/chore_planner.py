"""chore-planner-skill."""

from __future__ import annotations

from typing import Any

from ..memory import MemoryStore
from ..tools.chore_tools import generate_chore_schedule


def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    snapshot = memory.snapshot()
    schedule = generate_chore_schedule(
        user_input,
        snapshot["roommates"],
        snapshot["constraints"],
        snapshot.get("chores", []),
    )
    events = memory.record_chore_assignments(
        schedule["assignments"],
        schedule["fairness_score"],
    )

    rows = [
        {
            "任務": assignment["task"],
            "負責人": assignment["assignee"],
            "difficulty": assignment["difficulty"],
            "理由": assignment["reason"],
        }
        for assignment in schedule["assignments"]
    ]
    assignment_lines = [
        f"- {row['任務']}：{row['負責人']}（difficulty {row['difficulty']}）- {row['理由']}"
        for row in rows
    ]
    commentary = "\n".join(f"- {line}" for line in schedule["commentary"])
    line_message = "\n".join(
        ["本週家事排班："]
        + [f"- {assignment['assignee']}：{assignment['task']}" for assignment in schedule["assignments"]]
        + [f"公平分數：{schedule['fairness_score']} / 100"]
    )

    markdown = f"""
### chore-planner-skill：家事排班技能

**本週排班**
{chr(10).join(assignment_lines)}

**本週公平分數**：{schedule['fairness_score']} / 100

**系統評論**
{commentary}
""".strip()

    return {
        "intent": "chore_planner",
        "skill": "chore-planner-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": {"家事排班": rows},
        "tools_used": ["parse_chore_tasks", "generate_chore_schedule", "calculate_fairness_score"],
        "memory_updates": [f"chore_assigned events: {len(events)}"],
    }
