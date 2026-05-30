"""Simple guardrails for playful but respectful roommate outputs."""

from __future__ import annotations

from typing import Any


PERSONAL_ATTACK_TERMS = [
    "白癡",
    "智障",
    "低能",
    "廢物",
    "去死",
    "死胖子",
    "醜八怪",
    "垃圾人",
    "神經病",
    "你是垃圾",
]

SENSITIVE_TERMS = [
    "種族",
    "性別",
    "娘炮",
    "殘障",
    "疾病",
    "家庭背景",
    "爸媽",
    "外貌",
]

PRIVACY_TERMS = [
    "公布所有私人欠款",
    "所有私人欠款紀錄",
    "公開欠款紀錄",
    "銀行帳號",
    "身分證",
]

REAL_ACTION_TERMS = [
    "自動扣款",
    "直接扣款",
    "真的轉帳",
    "幫我轉帳",
    "強制收款",
]

LEGAL_TERMS = [
    "法律判決",
    "法律效力",
    "法院判決",
    "起訴",
]


def guardrail_check(text: str) -> dict[str, Any]:
    issues: list[str] = []

    if any(term in text for term in PERSONAL_ATTACK_TERMS):
        issues.append("contains_personal_attack")
    if any(term in text for term in SENSITIVE_TERMS):
        issues.append("mentions_sensitive_attribute")
    if any(term in text for term in PRIVACY_TERMS):
        issues.append("requests_private_debt_or_identity_info")
    if any(term in text for term in REAL_ACTION_TERMS):
        issues.append("requests_real_money_movement")
    legal_disclaimer_present = "不具法律效力" in text or "不是真正法律判決" in text
    if any(term in text for term in LEGAL_TERMS) and not legal_disclaimer_present:
        issues.append("implies_real_legal_authority")

    safe = not issues
    suggestion = "OK"
    if issues:
        suggestion = (
            "改成提醒任務與共同規則，不攻擊人格、不公開私人資料，"
            "分帳只提供建議，室友法庭只作為娛樂提醒且不具法律效力。"
        )

    return {"safe": safe, "issues": issues, "suggestion": suggestion}


def soften_for_group(text: str) -> str:
    """Remove harsh words from group announcements if a template ever gets spicy."""
    replacements = {
        "廢物": "需要提醒的室友",
        "白癡": "忘記任務的人",
        "智障": "需要協助的人",
        "低能": "需要重新確認任務的人",
        "去死": "請先冷靜一下",
        "垃圾人": "垃圾任務負責人",
        "你是垃圾": "垃圾任務需要處理",
    }
    softened = text
    for source, target in replacements.items():
        softened = softened.replace(source, target)
    return softened
