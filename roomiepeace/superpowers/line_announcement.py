"""LINE announcement skill."""

from __future__ import annotations

from typing import Any

from ..memory import MemoryStore
from ..tools.karma_tools import calculate_garbage_disaster_index
from ..tools.text_tools import join_names


def _latest_expense(memory_snapshot: dict[str, Any]) -> dict[str, Any] | None:
    expenses = memory_snapshot.get("expenses", [])
    return expenses[-1] if expenses else None


def _latest_chores(memory_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    chores = memory_snapshot.get("chores", [])
    if not chores:
        return []
    return chores[-1].get("assignments", [])


def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    snapshot = memory.snapshot()
    expense = _latest_expense(snapshot)
    chores = _latest_chores(snapshot)
    disaster_index = calculate_garbage_disaster_index(snapshot)

    sections = ["【本週 RoomiePeace 公告】"]
    expense_table = []
    if expense:
        shared_names = [item["name"] for item in expense.get("shared_items", [])]
        transfer_names = [transfer["from"] for transfer in expense.get("transfers", [])]
        sections.extend(
            [
                "",
                "1. 分帳",
                f"{expense['payer']}買了{join_names(shared_names)}，共 {expense['shared_total']:.0f} 元。",
                f"{join_names(transfer_names)}各轉{expense['payer']} {expense['transfer_amount']} 元。",
            ]
        )
        expense_table = [
            {"項目": item["name"], "金額": int(item["amount"])}
            for item in expense.get("shared_items", [])
        ]
    else:
        sections.extend(["", "1. 分帳", "本週目前沒有新的公費分帳。"])

    if chores:
        sections.extend(["", "2. 家事"])
        sections.extend([f"- {assignment['assignee']}：{assignment['task']}" for assignment in chores])
    else:
        sections.extend(["", "2. 家事", "本週尚未產生排班，請啟動家事排班技能。"])

    trash_assignee = next((assignment["assignee"] for assignment in chores if assignment["task"] == "倒垃圾"), "垃圾任務負責人")
    if disaster_index >= 70:
        trash_line = f"垃圾桶目前已接近副本 Boss 等級。請{trash_assignee}今晚處理，感謝各位維護人類文明。"
    else:
        trash_line = f"垃圾桶目前可控，請{trash_assignee}照排班完成即可。"

    sections.extend(["", "3. 系統提醒", trash_line, "", "提醒：分帳只提供建議，請大家自行確認後轉帳。"])
    line_message = "\n".join(sections)
    event = memory.record_announcement("本週 RoomiePeace 公告")

    markdown = f"""
### line-announcement-skill：LINE 群組公告

```text
{line_message}
```
""".strip()

    tables = {"家事": [{"負責人": item["assignee"], "任務": item["task"]} for item in chores]}
    if expense_table:
        tables["分帳項目"] = expense_table

    return {
        "intent": "line_announcement",
        "skill": "line-announcement-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": tables,
        "tools_used": ["latest_expense", "latest_chores", "calculate_garbage_disaster_index"],
        "memory_updates": [f"line_announcement_created event @ {event['timestamp']}"],
    }
