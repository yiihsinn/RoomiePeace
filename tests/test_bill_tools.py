from roomiepeace.tools.bill_tools import detect_payer, parse_receipt_items, split_bill


def test_receipt_splitter_demo_amounts_are_correct():
    roommates = ["阿明", "小美", "冠宇", "庭萱"]
    text = "阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65，幫我們分帳。"

    payer = detect_payer(text, roommates)
    items = parse_receipt_items(text)
    result = split_bill(items, payer, roommates)

    assert payer == "阿明"
    assert len(items) == 4
    assert result["shared_total"] == 353
    assert result["per_person"] == 88.25
    assert result["transfer_amount"] == 88
    assert [transfer["from"] for transfer in result["transfers"]] == ["小美", "冠宇", "庭萱"]
    assert all(transfer["amount"] == 88 for transfer in result["transfers"])
