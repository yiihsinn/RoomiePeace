"""roomie-court-skill."""

from __future__ import annotations

from typing import Any

from ..memory import MemoryStore
from ..tools.text_tools import extract_target, extract_topic


def _build_evidence(memory_snapshot: dict[str, Any], defendant: str, topic: str) -> list[str]:
    evidence = []
    for event in memory_snapshot.get("events", [])[-8:]:
        data = event.get("data", {})
        if defendant in str(data) and topic in str(data):
            if event.get("event_type") == "conflict_mediated":
                evidence.append("前次提醒已送達，但垃圾桶仍維持高存在感")
            if event.get("event_type") == "chore_assigned":
                evidence.append(f"{defendant}曾被正式排入{topic}任務，非自由心證")
    if topic == "倒垃圾":
        evidence.extend(
            [
                "垃圾桶已接近滿載狀態，並開始用沉默施壓",
                "廚房空氣品質提出口頭抗議，全體室友被迫旁聽",
            ]
        )
    if not evidence:
        evidence.append("共居規則需要被請回桌上，不然它會繼續裝沒事")
    return evidence[:3]


def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    snapshot = memory.snapshot()
    defendant = extract_target(user_input, snapshot["roommates"])
    topic = extract_topic(user_input)
    case_name = "垃圾桶滿到像小型掩埋場還被當裝置藝術案" if topic == "倒垃圾" else f"{topic}任務延宕但大家還要假裝冷靜案"
    evidence = _build_evidence(snapshot, defendant, topic)
    verdict = f"{defendant}需於今晚 23:00 前完成{topic}任務。"
    penalty = "若未完成，下週加派補衛生紙一次，並在群組回報：任務已完成，文明暫時保住。"
    reason = (
        "本庭認為，垃圾桶不是許願池，放著不會自動清空；室友和平也不是靠空氣清淨機硬撐。"
        if topic == "倒垃圾"
        else "本庭認為，共居和平需要有人按下完成鍵，不是靠大家一起裝忙。"
    )
    roast = (
        f"{defendant}目前不是壞人，只是和{topic}任務保持了過度穩定的遠距離關係。"
        if topic == "倒垃圾"
        else f"{defendant}目前不是被取消資格，只是需要跟{topic}任務重新建立連線。"
    )
    case = {
        "timestamp": memory.now(),
        "case_name": case_name,
        "defendant": defendant,
        "plaintiff": "全體室友、廚房空氣品質與被迫成熟的垃圾袋",
        "topic": topic,
        "evidence": evidence,
        "verdict": verdict,
        "penalty": penalty,
        "reason": reason,
        "roast": roast,
    }
    event = memory.record_court_case(case)

    evidence_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(evidence, start=1))
    line_message = (
        f"【室友法庭娛樂判決】\n"
        f"案件：{case_name}\n"
        f"被告：{defendant}\n"
        f"本庭吐槽：{roast}\n"
        f"判決：{verdict}\n"
        f"{penalty}\n"
        "提醒：本案只審任務，不審人格；本判決只作為共居娛樂與任務提醒，不具法律效力。"
    )
    markdown = f"""
### roomie-court-skill：室友法庭技能

【室友法庭開庭】

**案件名稱**：{case_name}  
**被告**：{defendant}  
**原告**：全體室友、廚房空氣品質與被迫成熟的垃圾袋

**證據**
{evidence_lines}

**本庭吐槽**
{roast}

**判決**  
{verdict}  
{penalty}

**判決理由**  
{reason}

_注意：室友法庭是娛樂與提醒，不是真正法律判決，也不具法律效力。_
""".strip()

    return {
        "intent": "roomie_court",
        "skill": "roomie-court-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": {
            "證據": [{"編號": index + 1, "內容": item} for index, item in enumerate(evidence)],
            "判決摘要": [
                {"欄位": "被告", "內容": defendant},
                {"欄位": "任務", "內容": topic},
                {"欄位": "本庭吐槽", "內容": roast},
                {"欄位": "懲罰", "內容": penalty},
            ],
        },
        "tools_used": ["extract_target", "extract_topic", "build_evidence", "guardrail_disclaimer"],
        "memory_updates": [f"court_case_created event @ {event['timestamp']}"],
    }
