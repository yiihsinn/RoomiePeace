"""Receipt parsing and bill-splitting tools."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


SHARED_ITEM_KEYWORDS = [
    "衛生紙", "洗衣精", "垃圾袋", "清潔劑", "洗碗精", 
    "菜瓜布", "抹布", "廚房紙巾", "沐浴乳", "洗手乳"
]

PERSONAL_ITEM_KEYWORDS = [
    "餅乾", "零食", "飲料", "便當", "咖啡", "手搖", "泡麵", "巧克力"
]


def detect_payer(text: str, roommates: list[str]) -> str:
    # 優化：允許名字前後有空格，且支援 1 到 10 個字的名字
    match = re.search(r"([一-龥A-Za-z1-9]{1,10})\s*(?:買了|幫大家買|先墊了?|墊了|付了|出了)", text)
    if match and match.group(1).strip() in roommates:
        return match.group(1).strip()

    for roommate in roommates:
        if roommate in text:
            return roommate
    return roommates[0]


def parse_receipt_items(text: str) -> list[dict[str, Any]]:
    """Extract item-price pairs from natural Chinese text."""
    segment = text
    for marker in ["買了", "幫大家買", "先墊了", "先墊", "墊了", "付了", "出了"]:
        if marker in text:
            segment = text.split(marker, 1)[1]
            break

    # 增加切分標點符號的容錯
    segment = re.split(r"[，,。；;]\s*(?:幫|請|麻煩|可以|分帳|算)", segment, maxsplit=1)[0]
    segment = segment.replace("，", "、").replace(",", "、").replace("；", "、")

    items: list[dict[str, Any]] = []
    known_items = sorted(SHARED_ITEM_KEYWORDS + PERSONAL_ITEM_KEYWORDS, key=len, reverse=True)
    known_pattern = "|".join(re.escape(item) for item in known_items)

    for chunk in _split_receipt_chunks(segment):
        # 進階正則：捕捉「品項(限定名字)100」或「品項100」
        # 範例：衛生紙(小美,庭萱,阿明)129元 -> group(1)="衛生紙(小美,庭萱,阿明)", group(2)="129"
        match = re.search(r"(.+?)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?$", chunk)
        if not match:
            if known_pattern:
                for known_match in re.finditer(rf"({known_pattern})\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?", chunk):
                    items.append(
                        {
                            "name": known_match.group(1).strip(),
                            "amount": float(known_match.group(2)),
                            "specific_members": None,
                        }
                    )
            continue
        
        raw_name = re.sub(r"^(和|以及|還有)", "", match.group(1).strip())
        amount = float(match.group(2))
        
        # 預設此品項由全體平分（None 代表後面 split_bill 會用全體 roommates 遞補）
        specific_members = None
        clean_name = raw_name
        
        # 進階解析：解析括號內指定特定人平分的語法，例如：冷氣費(阿明、小美)800
        member_match = re.search(r"[(（](.+?)[)）]", raw_name)
        if member_match:
            member_content = member_match.group(1)
            # 將常見的分隔符號統一替換成逗號
            member_content = re.sub(r"[、，,\s]", ",", member_content)
            specific_members = [m.strip() for m in member_content.split(",") if m.strip()]
            # 清理品項名稱，去掉括號部分，例如 "冷氣費(阿明、小美)" -> "冷氣費"
            clean_name = re.sub(r"[(（].+?[)）]", "", raw_name).strip()

        items.append({
            "name": clean_name, 
            "amount": amount,
            "specific_members": specific_members
        })
    return items


def _split_receipt_chunks(segment: str) -> list[str]:
    chunks: list[str] = []
    buffer: list[str] = []
    depth = 0
    for char in segment:
        if char in "(（":
            depth += 1
        elif char in ")）" and depth > 0:
            depth -= 1

        if char in "、,，；;" and depth == 0:
            chunk = "".join(buffer).strip()
            if chunk:
                chunks.append(chunk)
            buffer = []
            continue
        buffer.append(char)

    chunk = "".join(buffer).strip()
    if chunk:
        chunks.append(chunk)
    return chunks


def classify_item(item_name: str, roommates: list[str] = None) -> tuple[str, str | None]:
    """回傳 (分類, owner)。如果辨識出特定人名字，owner 就歸他"""
    # 檢查品項名中是否含有特定室友的名字（例如：冠宇的餅乾）
    detected_owner = None
    if roommates:
        for roommate in roommates:
            if roommate in item_name:
                detected_owner = roommate
                break

    if any(keyword in item_name for keyword in PERSONAL_ITEM_KEYWORDS):
        return "personal", detected_owner
    if any(keyword in item_name for keyword in SHARED_ITEM_KEYWORDS):
        return "shared", None
    
    # 預設為公用品，如果有指定名字則可能是代購的個人物品
    if detected_owner:
        return "personal", detected_owner
    return "shared", None


def _round_transfer(amount: float) -> int:
    decimal_amount = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(decimal_amount)


def split_bill(
    items: list[dict[str, Any]],
    payer: str,
    roommates: list[str],
) -> dict[str, Any]:
    classified_items = []
    
    # 用來記錄每個人「個別累積」需要支付給公帳的總金額
    # 初始化：每個人一開始都是 0 元
    debts: dict[str, float] = {rm: 0.0 for rm in roommates}

    for item in items:
        classification, owner = classify_item(item["name"], roommates)
        
        # 決定誰要分攤這筆錢
        if classification == "personal":
            # 如果是個人物品，看有沒有偵測到 owner，沒有的話預設是付款人 payer 買給自己的
            target_owner = owner if owner else payer
            item_members = [target_owner]
        else:
            # 如果是公用品，看有沒有在 parse 階段指定特定幾個人分，沒有的話就是 roommates 全體平分
            item_members = item["specific_members"] if item.get("specific_members") else roommates
        
        classified_items.append({
            "name": item["name"],
            "amount": item["amount"],
            "classification": classification,
            "owner": owner if owner else (payer if classification == "personal" else None),
            "split_members": item_members
        })

        # 計算每個人分攤的金額，並累加進 debts
        share_count = len(item_members)
        if share_count > 0:
            item_share = item["amount"] / share_count
            for member in item_members:
                if member in debts:
                    debts[member] += item_share

    shared_items = [item for item in classified_items if item["classification"] == "shared"]
    personal_items = [item for item in classified_items if item["classification"] == "personal"]
    
    # 浮點數精度安全加總
    shared_total = float(round(sum(item["amount"] for item in shared_items), 2))
    personal_total = float(round(sum(item["amount"] for item in personal_items), 2))
    
    # 標準全體平分時的每人應付金額（留給傳統文字顯示展示用）
    per_person = shared_total / len(roommates) if roommates else 0
    
    # 精確計算轉帳對象
    transfers = []
    for roommate, owed_amount in debts.items():
        if roommate != payer and owed_amount > 0:
            # 該室友應該轉給付款人的確定性整數金額
            rounded_amount = _round_transfer(owed_amount)
            transfers.append({
                "from": roommate,
                "to": payer,
                "amount": rounded_amount,
                "raw_amount": float(round(owed_amount, 2))
            })

    # 為了讓外層的 line_message 好處理，動態抓一個最主要的轉帳金額
    # 如果是非全體平分的彈性狀況，這裡取第一個轉帳金額作為參考，或者由 transfers 列表各自顯示
    transfer_amount = transfers[0]["amount"] if transfers else 0

    return {
        "payer": payer,
        "classified_items": classified_items,
        "shared_items": shared_items,
        "personal_items": personal_items,
        "shared_total": shared_total,
        "personal_total": personal_total,
        "per_person": per_person,             # 全體平均參考值
        "transfer_amount": transfer_amount,   # 單一轉帳金額參考值
        "transfers": transfers,               # 真正的轉帳清單（支援非全體平分！）
        "split_members": roommates,
    }
