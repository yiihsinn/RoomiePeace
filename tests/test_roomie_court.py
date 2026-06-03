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
