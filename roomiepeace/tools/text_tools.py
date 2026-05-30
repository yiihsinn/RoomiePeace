"""Small text helpers for deterministic templates."""

from __future__ import annotations

import re


def extract_roommates(text: str, fallback: list[str]) -> list[str]:
    known = [name for name in fallback if name in text]
    if known:
        return known

    match = re.search(r"室友[：:]\s*([^。]+)", text)
    if not match:
        return fallback
    candidates = [
        part.strip()
        for part in re.split(r"[、,，\s]+", match.group(1))
        if 1 < len(part.strip()) <= 4
    ]
    return candidates or fallback


def extract_constraints(text: str, roommates: list[str]) -> dict[str, str]:
    constraints: dict[str, str] = {}
    chunks = [chunk.strip() for chunk in re.split(r"[。；;，,]", text) if chunk.strip()]
    for roommate in roommates:
        for chunk in chunks:
            if roommate in chunk and any(keyword in chunk for keyword in ["期中考", "不在", "忘記", "限制"]):
                constraint = chunk.replace(roommate, "").strip(" ：:")
                constraints[roommate] = constraint or "無特殊限制"
    return constraints


def extract_target(text: str, roommates: list[str]) -> str:
    for roommate in roommates:
        if roommate in text:
            return roommate
    return roommates[0] if roommates else "某位室友"


def extract_topic(text: str) -> str:
    if "倒垃圾" in text or "垃圾" in text:
        return "倒垃圾"
    if "洗碗" in text:
        return "洗碗"
    if "拖地" in text:
        return "拖地"
    if "分帳" in text or "轉帳" in text:
        return "分帳"
    return "共居任務"


def join_names(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return "、".join(names)
