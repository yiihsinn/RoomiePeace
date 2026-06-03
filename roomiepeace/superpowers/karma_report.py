"""karma-report-skill."""

from __future__ import annotations

from typing import Any

from ..memory import MemoryStore
from ..tools.karma_tools import (
    build_karma_ranking,
    calculate_garbage_disaster_index,
    compute_karma,
)


def handle(_user_input: str, memory: MemoryStore) -> dict[str, Any]:
    snapshot = memory.snapshot()

    scores = compute_karma(snapshot)
    memory.set_karma(scores)

    # Refresh snapshot so all outputs reflect the recalculated Karma.
    snapshot = memory.snapshot()

    ranking = build_karma_ranking(snapshot)
    disaster_index = calculate_garbage_disaster_index(snapshot)

    ranking_lines = []

    if ranking:
        for index, row in enumerate(ranking, start=1):
            ranking_lines.append(
                f"{index}. **{row['roommate']}：{row['score']} 分**  \n"
                f"   稱號：{row['title']}  \n"
                f"   事蹟：{row['deed']}"
            )
    else:
        ranking_lines.append("目前還沒有足夠資料產生 Karma 排行榜。")

    if disaster_index < 55:
        status = "和平可維持"
    elif disaster_index < 75:
        status = "垃圾桶需要關注"
    else:
        status = "垃圾桶副本 Boss 等級"

    line_ranking = (
        [
            f"{index}. {row['roommate']}：{row['score']} 分｜{row['title']}"
            for index, row in enumerate(ranking, start=1)
        ]
        if ranking
        else ["目前還沒有足夠資料產生 Karma 排行榜。"]
    )

    line_message = "\n".join(
        ["本週 Roomie Karma 排行榜："]
        + line_ranking
        + [f"共居狀態：{status}（Garbage Disaster Index {disaster_index}/100）"]
    )

    ranking_markdown = "\n".join(ranking_lines)

    markdown = f"""
### karma-report-skill：Karma 排行榜技能

**本週 Roomie Karma 排行榜**

{ranking_markdown}

**本週共居狀態**：{status}  
**Garbage Disaster Index**：{disaster_index} / 100
""".strip()

    return {
        "intent": "karma_report",
        "skill": "karma-report-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": {"Karma 排行榜": ranking},
        "tools_used": [
            "compute_karma",
            "build_karma_ranking",
            "calculate_garbage_disaster_index",
        ],
        "memory_updates": ["karma scores recalculated"],
    }