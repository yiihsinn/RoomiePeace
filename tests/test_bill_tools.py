from roomiepeace.tools.bill_tools import detect_payer, parse_receipt_items, split_bill


def test_detect_payer_variants():
    """測試付款人辨識的各種文字容錯率（包含空格、多字、少字）"""
    roommates = ["阿明", "小美", "冠宇", "庭萱", "Bob"]
    
    # 測試 1：名字後面有空格
    assert detect_payer("阿明 買了衛生紙 100", roommates) == "阿明"
    # 測試 2：英文名字
    assert detect_payer("Bob買了洗衣精150", roommates) == "Bob"
    # 測試 3：沒有「買了」關鍵字，但提及名字（Fallback 邏輯）
    assert detect_payer("這筆是庭萱墊的總共200元", roommates) == "庭萱"
    # 測試 4：完全沒寫是誰，Fallback 到第一個室友
    assert detect_payer("買了垃圾袋65", roommates) == "阿明"


def test_split_bill_with_specific_members():
    """測試 Spec 17.1 要求：只有三人使用某項物品，不應四人平分"""
    roommates = ["阿明", "小美", "冠宇", "庭萱"]
    # 150 元由 3 人均分（各 50 元），冠宇不應該被收錢
    text = "阿明買了公用抹布(小美、庭萱、阿明)150元"
    
    payer = detect_payer(text, roommates)
    items = parse_receipt_items(text)
    result = split_bill(items, payer, roommates)
    
    assert payer == "阿明"
    assert items[0]["specific_members"] == ["小美", "庭萱", "阿明"]
    assert result["shared_total"] == 150
    
    # 檢查轉帳清單中，冠宇不應該存在（因為他不用付錢）
    transfers_dict = {t["from"]: t["amount"] for t in result["transfers"]}
    assert "小美" in transfers_dict
    assert "庭萱" in transfers_dict
    assert "冠宇" not in transfers_dict
    
    # 檢查金額是否正確被均分為 50 元
    assert transfers_dict["小美"] == 50
    assert transfers_dict["庭萱"] == 50


def test_split_bill_with_assigned_personal_owner():
    """測試幫特定室友代購個人物品，金額應精準算在該室友頭上"""
    roommates = ["阿明", "小美", "冠宇", "庭萱"]
    # 冠宇的飲料屬於個人物品，且 owner 應該是冠宇，50元該由冠宇全出
    text = "阿明買了冠宇的飲料50元"
    
    payer = detect_payer(text, roommates)
    items = parse_receipt_items(text)
    result = split_bill(items, payer, roommates)
    
    assert result["personal_total"] == 50
    assert result["classified_items"][0]["owner"] == "冠宇"
    
    transfers_dict = {t["from"]: t["amount"] for t in result["transfers"]}
    # 只有冠宇需要轉 50 元給阿明，其他人不用付
    assert transfers_dict.get("冠宇") == 50
    assert "小美" not in transfers_dict
    assert "庭萱" not in transfers_dict


def test_floating_point_precision_and_rounding():
    """測試除不盡時的 Decimal ROUND_HALF_UP 確定性四捨五入"""
    roommates = ["阿明", "小美", "冠宇"]  # 三個人
    # 公用品 100 元，100 / 3 = 33.3333... 應四捨五入為 33 元
    # 公用品 200 元，200 / 3 = 66.6666... 應五入為 67 元
    
    # 狀況 A：33.33 元 -> 33 元
    items_a = [{"name": "垃圾袋", "amount": 100.0}]
    result_a = split_bill(items_a, "阿明", roommates)
    assert result_a["transfers"][0]["amount"] == 33
    
    # 狀況 B：66.67 元 -> 67 元
    items_b = [{"name": "清潔劑", "amount": 200.0}]
    result_b = split_bill(items_b, "阿明", roommates)
    assert result_b["transfers"][0]["amount"] == 67


def test_all_items_are_personal_no_transfers():
    """測試極端狀況：如果買的所有東西都是付款人自己的個人物品，轉帳清單應為空"""
    roommates = ["阿明", "小美", "冠宇", "庭萱"]
    text = "阿明買了巧克力89、零食100"
    
    payer = detect_payer(text, roommates)
    items = parse_receipt_items(text)
    result = split_bill(items, payer, roommates)
    
    assert result["shared_total"] == 0
    assert result["personal_total"] == 189
    # 因為都是阿明自己買給自己吃的，其他人不需要轉帳給他 [cite: 291]
    assert len(result["transfers"]) == 0


def test_complex_mixed_sentence():
    """綜合測試：公用物品(全體)、公用物品(指定人)、個人物品(指定人)混在一起"""
    roommates = ["阿明", "小美", "冠宇", "庭萱"]
    # 衛生紙(公用全體): 120 -> 每人 30
    # 冷氣費(指定阿明小美): 200 -> 每人 100
    # 冠宇的便當(個人指定): 110 -> 冠宇付 110
    text = "阿明買了衛生紙120、冷氣費(阿明、小美)200、以及冠宇的便當110"
    
    payer = detect_payer(text, roommates)
    items = parse_receipt_items(text)
    result = split_bill(items, payer, roommates)
    
    # 應付總額驗證：
    # 小美要付：衛生紙 30 + 冷氣費 100 = 130 元
    # 冠宇要付：衛生紙 30 + 便當 110 = 140 元
    # 庭萱要付：衛生紙 30 = 30 元
    transfers_dict = {t["from"]: t["amount"] for t in result["transfers"]}
    
    assert transfers_dict["小美"] == 130
    assert transfers_dict["冠宇"] == 140
    assert transfers_dict["庭萱"] == 30