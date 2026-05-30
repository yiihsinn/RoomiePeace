"""Deterministic router for selecting RoomiePeace superpowers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteResult:
    intent: str
    selected_superpower: str
    reason: str


ROUTES = [
    (
        "setup_roommates",
        "roommate-setup",
        ["建立室友", "室友資料", "四個室友", "我們有", "成員"],
    ),
    (
        "line_announcement",
        "line-announcement-skill",
        ["LINE", "Line", "line", "群組公告", "公告", "整理成可以貼"],
    ),
    (
        "roomie_court",
        "roomie-court-skill",
        ["室友法庭", "法庭", "判決", "開庭", "裁決"],
    ),
    (
        "karma_report",
        "karma-report-skill",
        ["Karma", "karma", "排行榜", "排行", "分數", "稱號"],
    ),
    (
        "conflict_mediator",
        "conflict-mediator-skill",
        ["不想吵架", "提醒", "抱怨", "調解", "又忘記", "不要吵"],
    ),
    (
        "receipt_splitter",
        "receipt-splitter-skill",
        ["分帳", "買了", "收據", "公費", "轉帳", "共同支出"],
    ),
    (
        "chore_planner",
        "chore-planner-skill",
        ["家事", "排班", "倒垃圾", "拖地", "洗浴室", "補衛生紙"],
    ),
]


def route(user_input: str) -> RouteResult:
    text = user_input.strip()
    for intent, superpower, keywords in ROUTES:
        matched = [keyword for keyword in keywords if keyword in text]
        if matched:
            return RouteResult(
                intent=intent,
                selected_superpower=superpower,
                reason=f"matched keywords: {', '.join(matched[:3])}",
            )

    return RouteResult(
        intent="karma_report",
        selected_superpower="karma-report-skill",
        reason="fallback: no exact keyword, show current shared-living status",
    )
