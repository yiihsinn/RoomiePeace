"""conflict-mediator-skill."""

from __future__ import annotations

from typing import Any

from ..guardrails import soften_for_group
from ..memory import MemoryStore
from ..tools.text_tools import extract_target, extract_topic


def _risk_score(text: str) -> int:
    score = 45
    if "又" in text:
        score += 18
    if "每次" in text:
        score += 15
    if "不想吵架" in text:
        score += 8
    if "你" in text and "都" in text:
        score += 10
    return min(90, score)


def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    snapshot = memory.snapshot()
    target = extract_target(user_input, snapshot["roommates"])
    topic = extract_topic(user_input)
    risk = _risk_score(user_input)
    event = memory.record_conflict(target, topic, risk)

    if topic == "倒垃圾":
        gentle = f"{target}～提醒一下今天垃圾好像輪到你，現在有點滿了，你方便等等拿下去嗎？感謝！"
        group = f"本日垃圾任務提醒：{target}負責倒垃圾。垃圾桶目前已接近滿載，請今日睡前處理，感謝配合。"
        playful = f"{target}～垃圾桶目前已經進入最終型態，拜託你今晚拯救一下人類文明。"
    else:
        gentle = f"{target}～提醒一下 {topic} 這件事可能需要你協助，方便今天處理一下嗎？謝謝！"
        group = f"本日共居任務提醒：{target}負責{topic}，請今日完成，感謝配合。"
        playful = f"{target}～{topic}任務已經亮起提示燈，拜託你幫大家按一下完成鍵。"

    group = soften_for_group(group)
    playful = soften_for_group(playful)
    line_message = group

    markdown = f"""
### conflict-mediator-skill：衝突調解技能

**語氣風險分析**  
直接說「你每次都不處理」可能造成 **{risk}%** 的防衛反應。建議改成提醒任務，不攻擊人格。

**溫柔版**  
{gentle}

**群組公告版**  
{group}

**嘴砲但不失禮版**  
{playful}

**推薦版本**：先用溫柔版私訊；如果今天睡前還沒處理，再把群組公告版貼到群組。
""".strip()

    return {
        "intent": "conflict_mediator",
        "skill": "conflict-mediator-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": {
            "提醒版本": [
                {"版本": "溫柔版", "內容": gentle},
                {"版本": "群組公告版", "內容": group},
                {"版本": "嘴砲但不失禮版", "內容": playful},
            ]
        },
        "tools_used": ["extract_target", "extract_topic", "tone_risk_score", "soften_for_group"],
        "memory_updates": [f"conflict_mediated event @ {event['timestamp']}"],
    }
