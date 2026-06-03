"""Demo scenario loading for Guided Demo UI."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO_PATH = PROJECT_ROOT / "data" / "demo_scenarios.json"


DEFAULT_DEMO_SCENARIO: dict[str, Any] = {
    "scenario_name": "冠宇與垃圾桶事件",
    "description": "從建立室友資料開始，依序展示分帳、家事、衝突調解、室友法庭、LINE 公告與 Karma。",
    "steps": [
        {
            "id": "setup_roommates",
            "title": "建立室友資料",
            "purpose": "建立四位室友與本週限制，讓後續 skills 都能讀取同一份 memory。",
            "prompt": "我們有四個室友：阿明、小美、冠宇、庭萱。小美這週期中考，阿明週三晚上不在，冠宇常常忘記倒垃圾。",
            "expected_intent": "setup_roommates",
            "expected_skill": "roommate-setup",
        },
        {
            "id": "receipt_splitter",
            "title": "分帳 demo",
            "purpose": "展示 receipt-splitter-skill 解析品項、分類公用品並用 tool 精準分帳。",
            "prompt": "阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65，幫我們分帳。",
            "expected_intent": "receipt_splitter",
            "expected_skill": "receipt-splitter-skill",
        },
        {
            "id": "chore_planner",
            "title": "家事排班 demo",
            "purpose": "展示 chore-planner-skill 根據限制與 difficulty 產生公平排班。",
            "prompt": "幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。",
            "expected_intent": "chore_planner",
            "expected_skill": "chore-planner-skill",
        },
        {
            "id": "conflict_mediator",
            "title": "衝突調解 demo",
            "purpose": "展示 conflict-mediator-skill 把抱怨轉成有效但不傷感情的提醒。",
            "prompt": "冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。",
            "expected_intent": "conflict_mediator",
            "expected_skill": "conflict-mediator-skill",
        },
        {
            "id": "roomie_court",
            "title": "室友法庭 demo",
            "purpose": "展示 roomie-court-skill 讀取前面 memory，對累犯任務做加重但不霸凌的娛樂判決。",
            "prompt": "啟動室友法庭，幫我判決冠宇不倒垃圾。",
            "expected_intent": "roomie_court",
            "expected_skill": "roomie-court-skill",
        },
        {
            "id": "line_announcement",
            "title": "LINE 群組公告",
            "purpose": "展示 line-announcement-skill 從 memory 彙整分帳、家事與垃圾提醒。",
            "prompt": "幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。",
            "expected_intent": "line_announcement",
            "expected_skill": "line-announcement-skill",
        },
        {
            "id": "karma_report",
            "title": "Karma 排行榜",
            "purpose": "展示 karma-report-skill 根據 event-based memory 產生排行榜和稱號。",
            "prompt": "產生本週 Karma 排行榜。",
            "expected_intent": "karma_report",
            "expected_skill": "karma-report-skill",
        },
    ],
}


REQUIRED_STEP_FIELDS = {
    "id",
    "title",
    "purpose",
    "prompt",
    "expected_intent",
    "expected_skill",
}


def validate_demo_scenario(scenario: dict[str, Any]) -> None:
    if not scenario.get("scenario_name"):
        raise ValueError("scenario_name is required")
    if not isinstance(scenario.get("steps"), list) or not scenario["steps"]:
        raise ValueError("steps must be a non-empty list")

    for index, step in enumerate(scenario["steps"], start=1):
        missing = REQUIRED_STEP_FIELDS - set(step)
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"step {index} missing fields: {missing_fields}")


def load_demo_scenario(path: str | Path | None = None) -> dict[str, Any]:
    scenario_path = Path(path) if path else DEFAULT_SCENARIO_PATH
    try:
        with scenario_path.open("r", encoding="utf-8") as file:
            scenario = json.load(file)
        validate_demo_scenario(scenario)
        return scenario
    except (OSError, json.JSONDecodeError, ValueError):
        return deepcopy(DEFAULT_DEMO_SCENARIO)
