"""Optional Gemini-on-Vertex NLU with deterministic fallback.

Gemini extracts structured task fields. It does not calculate bill splits,
assign chores, mutate memory, or decide final outputs.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from .router import route
from .tools.bill_tools import detect_payer, parse_receipt_items
from .tools.text_tools import extract_target, extract_topic


INTENT_TO_SKILL = {
    "setup_roommates": "roommate-setup",
    "receipt_splitter": "receipt-splitter-skill",
    "chore_planner": "chore-planner-skill",
    "conflict_mediator": "conflict-mediator-skill",
    "roomie_court": "roomie-court-skill",
    "karma_report": "karma-report-skill",
    "line_announcement": "line-announcement-skill",
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_NLU_CACHE_PATH = PROJECT_ROOT / "data" / "demo_nlu_cache.json"


@dataclass
class NLUResult:
    intent: str
    confidence: float
    data: dict[str, Any]
    source: str
    missing_fields: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def selected_superpower(self) -> str:
        return INTENT_TO_SKILL.get(self.intent, "unknown")

    def to_trace(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "intent": self.intent,
            "confidence": round(float(self.confidence), 2),
            "missing_fields": self.missing_fields,
            "data": self.data,
            "notes": self.notes,
        }


GEMINI_NLU_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "enum": [
                "setup_roommates",
                "receipt_splitter",
                "chore_planner",
                "conflict_mediator",
                "roomie_court",
                "karma_report",
                "line_announcement",
                "unknown",
            ],
        },
        "confidence": {"type": "NUMBER", "minimum": 0, "maximum": 1},
        "payer": {"type": "STRING"},
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "amount": {"type": "NUMBER"},
                    "classification": {
                        "type": "STRING",
                        "enum": ["shared", "personal", "unknown"],
                    },
                },
                "required": ["name", "amount", "classification"],
            },
        },
        "target": {"type": "STRING"},
        "topic": {"type": "STRING"},
        "tone": {"type": "STRING"},
        "missing_fields": {"type": "ARRAY", "items": {"type": "STRING"}},
        "notes": {"type": "STRING"},
    },
    "required": [
        "intent",
        "confidence",
        "payer",
        "items",
        "target",
        "topic",
        "tone",
        "missing_fields",
        "notes",
    ],
}


def extract_task(user_input: str, roommates: list[str]) -> NLUResult:
    _load_dotenv()
    cached_result = _extract_from_demo_cache(user_input)
    if cached_result:
        return cached_result
    if _vertex_env_ready():
        gemini_result = _extract_with_vertex_gemini(user_input, roommates)
        if gemini_result:
            return gemini_result
    return fallback_extract_task(user_input, roommates)


def fallback_extract_task(user_input: str, roommates: list[str]) -> NLUResult:
    route_result = route(user_input)
    items = parse_receipt_items(user_input)
    intent = route_result.intent

    if items and intent == "karma_report":
        intent = "receipt_splitter"

    payer = detect_payer(user_input, roommates) if items or intent == "receipt_splitter" else ""
    target = extract_target(user_input, roommates) if any(name in user_input for name in roommates) else ""
    topic = extract_topic(user_input)

    missing_fields: list[str] = []
    confidence = 0.65 if route_result.intent != "karma_report" else 0.35

    if intent == "receipt_splitter":
        if not payer:
            missing_fields.append("payer")
        if not items:
            missing_fields.append("items")
        confidence = 0.82 if payer and items else 0.42
    elif intent in {"conflict_mediator", "roomie_court"}:
        if not target:
            missing_fields.append("target")
        if topic == "共居任務":
            missing_fields.append("topic")
        confidence = 0.78 if not missing_fields else 0.48
    elif intent == "chore_planner":
        confidence = 0.75
    elif intent in {"line_announcement", "karma_report", "setup_roommates"}:
        confidence = 0.8

    return NLUResult(
        intent=intent,
        confidence=confidence,
        data={
            "payer": payer,
            "items": items,
            "target": target,
            "topic": topic,
            "tone": "funny but polite",
        },
        source="deterministic_fallback",
        missing_fields=missing_fields,
        notes="Vertex Gemini NLU unavailable; deterministic fallback used.",
    )


def _extract_with_vertex_gemini(user_input: str, roommates: list[str]) -> NLUResult | None:
    try:
        from google import genai
        from google.genai.types import HttpOptions
    except ImportError:
        return None

    model = os.getenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f"""
Extract one RoomiePeace task from the user input.

Rules:
- Return only fields in the response schema.
- Do not calculate bill splits. Only extract payer and item amounts.
- Use empty strings or empty arrays for unknown fields.
- Classification: shared for common household goods, personal for private food/drinks/snacks, unknown when unclear.
- Topic examples: 倒垃圾, 洗碗, 拖地, 洗浴室, 補衛生紙, 分帳.
- Known roommates: {", ".join(roommates)}.

User input:
{user_input}
""".strip()

    try:
        client = genai.Client(http_options=HttpOptions(api_version="v1"))
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_schema": GEMINI_NLU_SCHEMA,
            },
        )
    except Exception:
        return None

    try:
        parsed = json.loads(response.text or "{}")
    except (TypeError, json.JSONDecodeError):
        return None

    intent = parsed.get("intent", "unknown")
    if intent == "unknown":
        fallback = fallback_extract_task(user_input, roommates)
        fallback.source = "gemini_unknown_fallback"
        fallback.notes = "Gemini returned unknown intent; deterministic fallback used."
        return fallback

    data = {
        "payer": parsed.get("payer", ""),
        "items": [
            {
                "name": item.get("name", ""),
                "amount": _safe_float(item.get("amount", 0)),
                "classification": item.get("classification", "unknown"),
            }
            for item in parsed.get("items", [])
            if item.get("name") and _safe_float(item.get("amount", 0)) > 0
        ],
        "target": parsed.get("target", ""),
        "topic": parsed.get("topic", ""),
        "tone": parsed.get("tone", "funny but polite"),
    }
    missing_fields = list(parsed.get("missing_fields", []))
    if intent == "receipt_splitter" and not data["items"] and "items" not in missing_fields:
        missing_fields.append("items")
    if intent in {"conflict_mediator", "roomie_court"} and not data["target"] and "target" not in missing_fields:
        missing_fields.append("target")

    return NLUResult(
        intent=intent,
        confidence=float(parsed.get("confidence", 0)),
        data=data,
        source="vertex_gemini_structured_output",
        missing_fields=missing_fields,
        notes=parsed.get("notes", ""),
    )


def _extract_from_demo_cache(user_input: str) -> NLUResult | None:
    if os.getenv("ROOMIEPEACE_DISABLE_DEMO_NLU_CACHE") == "1":
        return None

    entry = _load_demo_nlu_cache().get(_normalize_prompt(user_input))
    if not entry:
        return None

    data = entry.get("data", {})
    return NLUResult(
        intent=entry.get("intent", "unknown"),
        confidence=float(entry.get("confidence", 0)),
        data={
            "payer": data.get("payer", ""),
            "items": [
                {
                    "name": item.get("name", ""),
                    "amount": _safe_float(item.get("amount", 0)),
                    "classification": item.get("classification", "unknown"),
                }
                for item in data.get("items", [])
                if item.get("name") and _safe_float(item.get("amount", 0)) > 0
            ],
            "target": data.get("target", ""),
            "topic": data.get("topic", ""),
            "tone": data.get("tone", "funny but polite"),
        },
        source="cached_vertex_gemini_structured_output",
        missing_fields=list(entry.get("missing_fields", [])),
        notes=entry.get("notes", "Cached Gemini extraction for demo replay."),
    )


@lru_cache(maxsize=1)
def _load_demo_nlu_cache() -> dict[str, dict[str, Any]]:
    try:
        with DEMO_NLU_CACHE_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    entries: dict[str, dict[str, Any]] = {}
    for entry in payload.get("entries", []):
        prompt = entry.get("prompt", "")
        if prompt:
            entries[_normalize_prompt(prompt)] = entry
    return entries


def _normalize_prompt(text: str) -> str:
    return " ".join(text.strip().split())


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(PROJECT_ROOT / ".env")


def _vertex_env_ready() -> bool:
    if os.getenv("ROOMIEPEACE_DISABLE_LLM_NLU") == "1":
        return False
    return all(
        os.getenv(name)
        for name in [
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
        ]
    )


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
