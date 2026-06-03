"""receipt-splitter-skill."""

from __future__ import annotations

from typing import Any

from ..memory import MemoryStore
from ..tools.bill_tools import detect_payer, parse_receipt_items, split_bill
from ..tools.text_tools import join_names


def handle(user_input: str, memory: MemoryStore, nlu_data: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = memory.snapshot()
    roommates = snapshot["roommates"]
    nlu_data = nlu_data or {}
    payer = nlu_data.get("payer") or detect_payer(user_input, roommates)
    items = nlu_data.get("items") or parse_receipt_items(user_input)
    split = split_bill(items, payer, roommates)

    # 1. 記錄事件到 Event Log (Memory)
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

    # 2. 預先處理字串，避免 f-string 內包含反斜線 (Python 舊版相容性)
    item_lines = []
    for item in split["classified_items"]:
        # 支援讀取個人物品的真正 owner，若無則歸給 payer
        if item["classification"] == "shared":
            label = "公用品"
        else:
            owner = item.get("owner", payer)
            label = f"{owner}個人物品"
        item_lines.append(f"- {item['name']}：{label}，{item['amount']:.0f} 元")
    items_str = "\n".join(item_lines)

    transfer_lines = [
        f"- {transfer['from']} 轉給 {payer}：{transfer['amount']} 元"
        for transfer in split["transfers"]
    ]
    transfers_str = "\n".join(transfer_lines) if transfer_lines else "- 無需轉帳"

    # 3. 組裝 LINE 訊息
    personal_note = ""
    if personal_items := split["personal_items"]:
        # 這裡進一步精細化：如果是幫別人買的也可以動態調配
        owners = {item.get("owner", payer) for item in personal_items}
        owners_str = join_names(list(owners))
        personal_note = f"\n{join_names(personal_names)}是 {owners_str} 自己的項目，不列入公費。"

    if transfer_names:
        transfer_instruction = f"{join_names(transfer_names)}各轉 {payer} {int(split['transfer_amount'])} 元就好。"
    else:
        transfer_instruction = "本次無產生需要轉帳的款項。"

    line_message = (
        f"{payer}剛剛買了{join_names(shared_names)}，共 {split['shared_total']:.0f} 元。\n"
        f"{transfer_instruction}"
        f"{personal_note}\n"
        "提醒：這只是分帳建議，RoomiePeace 不會執行真實轉帳。"
    )

    # 4. 組裝 Markdown 回應
    markdown = f"""
### receipt-splitter-skill：分帳技能

**品項判斷**
{items_str}

**公費總額**：{split['shared_total']:.0f} 元  
**{len(roommates)} 人平分**：每人 {split['per_person']:.2f} 元  
**建議轉帳**
{transfers_str}

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
        # 保持與程式碼 import 的工具一致
        "tools_used": ["detect_payer", "parse_receipt_items", "split_bill"],
        "memory_updates": [
            f"expense_created event @ {event['timestamp'] if event else memory.now()}",
            f"{payer} karma +2 (墊付獎勵)",
            f"inventory updated: {join_names(shared_names)}",
        ],
    }