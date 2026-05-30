from roomiepeace.router import route


def test_router_receipt_splitter():
    result = route("阿明買了衛生紙129，幫我們分帳")
    assert result.intent == "receipt_splitter"
    assert result.selected_superpower == "receipt-splitter-skill"


def test_router_chore_planner():
    result = route("幫我們排這週家事")
    assert result.intent == "chore_planner"


def test_router_conflict_mediator():
    result = route("冠宇又忘記倒垃圾，但我不想吵架，幫我提醒他")
    assert result.intent == "conflict_mediator"


def test_router_roomie_court():
    result = route("啟動室友法庭，幫我判決冠宇不倒垃圾")
    assert result.intent == "roomie_court"


def test_router_karma_report():
    result = route("產生 Karma 排行榜")
    assert result.intent == "karma_report"
