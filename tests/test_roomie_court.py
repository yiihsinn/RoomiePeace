from roomiepeace import MemoryStore, RoomiePeaceAgent


def test_roomie_court_is_sharper_but_guardrail_safe(tmp_path):
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    result = agent.handle("啟動室友法庭，幫我判決冠宇不倒垃圾。")

    assert result["trace"]["intent"] == "roomie_court"
    assert result["trace"]["guardrail_result"]["safe"] is True
    assert "垃圾桶不是許願池" in result["response_markdown"]
    assert "本案只審任務，不審人格" in result["line_message"]
    assert "判決摘要" in result["tables"]
    assert "累犯指數" in result["response_markdown"]


def test_roomie_court_escalates_repeat_offender_from_demo_memory(tmp_path):
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    agent.handle("幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。")
    agent.handle("冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。")
    result = agent.handle("啟動室友法庭，幫我判決冠宇不倒垃圾。")

    assert result["trace"]["guardrail_result"]["safe"] is True
    assert "累犯指數：3（累犯加重）" in result["response_markdown"]
    assert "累犯加重" in result["line_message"]
    assert "垃圾袋庫存盤點" in result["line_message"]
    assert len(result["tables"]["累犯紀錄"]) == 3

    announcement = agent.handle("幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。")
    assert "室友法庭" in announcement["line_message"]
    assert "累犯指數：3" in announcement["line_message"]
    assert "室友法庭" in announcement["tables"]
