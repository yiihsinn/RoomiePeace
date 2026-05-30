"""Karma and dashboard scoring tools."""

from __future__ import annotations

from typing import Any


def calculate_garbage_disaster_index(memory: dict[str, Any]) -> int:
    index = 35
    inventory = memory.get("inventory", {})
    if "已用完" in inventory.get("垃圾袋", ""):
        index += 20
    if "剛補貨" in inventory.get("垃圾袋", ""):
        index -= 10

    recent_events = memory.get("events", [])[-10:]
    for event in recent_events:
        data = event.get("data", {})
        text = " ".join(str(value) for value in data.values())
        if "倒垃圾" in text and event.get("event_type") in {"conflict_mediated", "court_case_created"}:
            index += 18
        if event.get("event_type") == "chore_assigned" and data.get("chore") == "倒垃圾":
            index -= 5

    return max(0, min(100, index))


def compute_karma(memory: dict[str, Any]) -> dict[str, int]:
    scores = dict(memory.get("karma", {}))
    for name in memory.get("roommates", []):
        scores.setdefault(name, 70)

    for event in memory.get("events", []):
        event_type = event.get("event_type")
        actor = event.get("actor")
        data = event.get("data", {})
        if event_type == "expense_created" and actor in scores:
            scores[actor] += 1
        if event_type == "chore_assigned":
            assignee = data.get("assigned_to")
            if assignee in scores:
                scores[assignee] += max(1, int(data.get("difficulty", 1)))
        if event_type == "conflict_mediated":
            target = data.get("target")
            if target in scores:
                scores[target] -= 1
        if event_type == "court_case_created":
            defendant = data.get("defendant")
            if defendant in scores:
                scores[defendant] -= 2

    return {name: max(0, min(100, int(score))) for name, score in scores.items()}


def title_for_roommate(name: str, score: int, memory: dict[str, Any]) -> str:
    constraint = memory.get("constraints", {}).get(name, "")
    if "期中考" in constraint:
        return "考試週保護名額"
    if "忘記倒垃圾" in constraint or score < 55:
        return "垃圾桶觀察家"
    if score >= 90:
        return "公用品守護者"
    if score >= 80:
        return "穩定輸出型室友"
    return "和平維持實習生"


def deed_for_roommate(name: str, memory: dict[str, Any]) -> str:
    events = memory.get("events", [])
    if any(event.get("actor") == name and event.get("event_type") == "expense_created" for event in events):
        return "主動補公用品，讓大家不用面對空空如也的架子。"
    if any(
        event.get("event_type") == "chore_assigned"
        and event.get("data", {}).get("assigned_to") == name
        and event.get("data", {}).get("chore") == "洗浴室"
        for event in events
    ):
        return "承接高 difficulty 任務，值得掌聲。"
    constraint = memory.get("constraints", {}).get(name, "")
    if "期中考" in constraint:
        return "因期中考減輕家事，系統暫不追究。"
    if "忘記倒垃圾" in constraint:
        return "多次觀察垃圾桶，但互動頻率仍可提升。"
    return "本週狀態穩定，沒有製造新的共居支線。"


def build_karma_ranking(memory: dict[str, Any]) -> list[dict[str, Any]]:
    scores = compute_karma(memory)
    rows = []
    for name, score in scores.items():
        rows.append(
            {
                "roommate": name,
                "score": score,
                "title": title_for_roommate(name, score, memory),
                "deed": deed_for_roommate(name, memory),
            }
        )
    return sorted(rows, key=lambda row: row["score"], reverse=True)
