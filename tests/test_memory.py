from roomiepeace import MemoryStore, RoomiePeaceAgent


def test_receipt_skill_adds_expense_event(tmp_path):
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    agent.handle("阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65，幫我們分帳。")
    snapshot = memory.snapshot()

    assert len(snapshot["expenses"]) == 1
    assert any(event["event_type"] == "expense_created" for event in snapshot["events"])


def test_chore_skill_adds_chore_events(tmp_path):
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    result = agent.handle("幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。")
    snapshot = memory.snapshot()

    assert len(snapshot["chores"]) == 1
    chore_events = [event for event in snapshot["events"] if event["event_type"] == "chore_assigned"]
    assert len(chore_events) == 4
    assert len(result["tables"]["近期負擔總覽"]) == 4
    assert result["trace"]["selected_superpower"] == "chore-planner-skill"
