"""Receipt parsing and bill-splitting tools."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


SHARED_ITEM_KEYWORDS = [
    "衛生紙",
    "洗衣精",
    "垃圾袋",
    "清潔劑",
    "洗碗精",
    "菜瓜布",
    "抹布",
    "廚房紙巾",
    "沐浴乳",
    "洗手乳",
]

PERSONAL_ITEM_KEYWORDS = [
    "餅乾",
    "零食",
    "飲料",
    "便當",
    "咖啡",
    "手搖",
    "泡麵",
    "巧克力",
]


def detect_payer(text: str, roommates: list[str]) -> str:
    match = re.search(r"([一-龥A-Za-z]{2,6})買了", text)
    if match and match.group(1) in roommates:
        return match.group(1)

    for roommate in roommates:
        if roommate in text:
            return roommate
    return roommates[0]


def parse_receipt_items(text: str) -> list[dict[str, Any]]:
    """Extract item-price pairs from natural Chinese text."""
    segment = text
    if "買了" in text:
        segment = text.split("買了", 1)[1]
    segment = re.split(r"[，,。；;]\s*(?:幫|請|麻煩|可以|分帳|算)", segment, maxsplit=1)[0]
    segment = segment.replace("，", "、").replace(",", "、").replace("；", "、")

    items: list[dict[str, Any]] = []
    for chunk in [part.strip() for part in segment.split("、") if part.strip()]:
        match = re.search(r"(.+?)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?$", chunk)
        if not match:
            continue
        name = re.sub(r"^(和|以及|還有)", "", match.group(1).strip())
        amount = float(match.group(2))
        items.append({"name": name, "amount": amount})
    return items


def classify_item(item_name: str) -> str:
    if any(keyword in item_name for keyword in PERSONAL_ITEM_KEYWORDS):
        return "personal"
    if any(keyword in item_name for keyword in SHARED_ITEM_KEYWORDS):
        return "shared"
    return "shared"


def _round_transfer(amount: float) -> int:
    decimal_amount = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(decimal_amount)


def split_bill(
    items: list[dict[str, Any]],
    payer: str,
    roommates: list[str],
) -> dict[str, Any]:
    classified_items = []
    for item in items:
        classification = classify_item(item["name"])
        classified_items.append({**item, "classification": classification})

    shared_items = [item for item in classified_items if item["classification"] == "shared"]
    personal_items = [item for item in classified_items if item["classification"] == "personal"]
    shared_total = sum(item["amount"] for item in shared_items)
    personal_total = sum(item["amount"] for item in personal_items)
    per_person = shared_total / len(roommates) if roommates else 0
    transfer_amount = _round_transfer(per_person)

    transfers = [
        {"from": roommate, "to": payer, "amount": transfer_amount, "raw_amount": per_person}
        for roommate in roommates
        if roommate != payer
    ]

    return {
        "payer": payer,
        "classified_items": classified_items,
        "shared_items": shared_items,
        "personal_items": personal_items,
        "shared_total": shared_total,
        "personal_total": personal_total,
        "per_person": per_person,
        "transfer_amount": transfer_amount,
        "transfers": transfers,
        "split_members": roommates,
    }
