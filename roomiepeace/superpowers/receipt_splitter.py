"""receipt-splitter-skill."""

from __future__ import annotations

from typing import Any

from ..memory import MemoryStore
from ..tools.bill_tools import detect_payer, parse_receipt_items, split_bill
from ..tools.text_tools import join_names


def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    snapshot = memory.snapshot()
    roommates = snapshot["roommates"]
    payer = detect_payer(user_input, roommates)
    items = parse_receipt_items(user_input)
    split = split_bill(items, payer, roommates)

    event = memory.record_expense(
        {
            "timestamp": memory.now(),
            "payer": payer,
            "classified_items": split["classified_items"],
            "shared_items": split["shared_items"],
            "personal_items": split["personal_items"],
            "shared_total": split["shared_total"],
            "personal_total": split["personal_total"],
            "per_person": split["per_person"],
            "transfer_amount": split["transfer_amount"],
            "transfers": split["transfers"],
            "split_members": split["split_members"],
        }
    )

    shared_names = [item["name"] for item in split["shared_items"]]
    personal_names = [item["name"] for item in split["personal_items"]]
    transfer_names = [transfer["from"] for transfer in split["transfers"]]

    item_lines = []
    for item in split["classified_items"]:
        label = "公用品" if item["classification"] == "shared" else f"{payer}個人物品"
        item_lines.append(f"- {item['name']}：{label}，{item['amount']:.0f} 元")

    transfer_lines = [
        f"- {transfer['from']} 轉給 {payer}：{transfer['amount']} 元"
        for transfer in split["transfers"]
    ]

    personal_note = ""
    if personal_names:
        personal_note = f"\n{join_names(personal_names)}是{payer}自己的快樂，不列入公費。"

    line_message = (
        f"{payer}剛剛買了{join_names(shared_names)}，共 {split['shared_total']:.0f} 元。\n"
        f"{join_names(transfer_names)}各轉{payer} {split['transfer_amount']} 元就好。"
        f"{personal_note}\n"
        "提醒：這只是分帳建議，RoomiePeace 不會執行真實轉帳。"
    )

    markdown = f"""
### receipt-splitter-skill：分帳技能

**品項判斷**
{chr(10).join(item_lines)}

**公費總額**：{split['shared_total']:.0f} 元  
**{len(roommates)} 人平分**：每人 {split['per_person']:.2f} 元  
**建議轉帳**
{chr(10).join(transfer_lines)}

**LINE 版**

{line_message}
""".strip()

    return {
        "intent": "receipt_splitter",
        "skill": "receipt-splitter-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": {
            "品項判斷": [
                {
                    "品項": item["name"],
                    "金額": int(item["amount"]),
                    "分類": "公用品" if item["classification"] == "shared" else "個人物品",
                }
                for item in split["classified_items"]
            ],
            "轉帳建議": [
                {"from": transfer["from"], "to": transfer["to"], "amount": transfer["amount"]}
                for transfer in split["transfers"]
            ],
        },
        "tools_used": ["detect_payer", "parse_receipt_items", "classify_item", "split_bill"],
        "memory_updates": [
            f"expense_created event @ {event['timestamp']}",
            f"{payer} karma +2",
            f"inventory updated: {join_names(shared_names)}",
        ],
    }
