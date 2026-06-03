from roomiepeace import MemoryStore, RoomiePeaceAgent
from roomiepeace.demo_scenarios import load_demo_scenario
from roomiepeace.nlu import extract_task, fallback_extract_task
from roomiepeace.tools.bill_tools import parse_receipt_items


def test_fallback_parser_handles_looser_receipt_format():
    text = "今天阿明先墊了公共用品，衛生紙129元，洗衣精159元，垃圾袋65元，餅乾89是他自己的，幫大家算一下"

    items = parse_receipt_items(text)

    assert {item["name"] for item in items} == {"衛生紙", "洗衣精", "垃圾袋", "餅乾"}
    assert sum(item["amount"] for item in items) == 442


def test_fallback_nlu_extracts_receipt_fields_without_llm():
    result = fallback_extract_task(
        "今天阿明先墊了公共用品，衛生紙129元，洗衣精159元，垃圾袋65元，餅乾89是他自己的，幫大家算一下",
        ["阿明", "小美", "冠宇", "庭萱"],
    )

    assert result.source == "deterministic_fallback"
    assert result.intent == "receipt_splitter"
    assert result.data["payer"] == "阿明"
    assert len(result.data["items"]) == 4


def test_demo_prompt_uses_cached_gemini_extraction_without_live_api():
    scenario = load_demo_scenario()
    receipt_step = next(step for step in scenario["steps"] if step["id"] == "receipt_splitter")

    result = extract_task(receipt_step["prompt"], ["阿明", "小美", "冠宇", "庭萱"])

    assert result.source == "cached_vertex_gemini_structured_output"
    assert result.intent == "receipt_splitter"
    assert result.data["payer"] == "阿明"
    assert [item["name"] for item in result.data["items"]] == ["衛生紙", "洗衣精", "垃圾袋", "餅乾"]


def test_agent_demo_prompt_uses_cached_gemini_trace(tmp_path):
    scenario = load_demo_scenario()
    receipt_step = next(step for step in scenario["steps"] if step["id"] == "receipt_splitter")
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    result = agent.handle(receipt_step["prompt"])

    assert result["trace"]["nlu_result"]["source"] == "cached_vertex_gemini_structured_output"
    assert "公費總額**：353 元" in result["response_markdown"]


def test_agent_asks_for_clarification_when_receipt_items_missing(tmp_path):
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    result = agent.handle("幫我分帳")

    assert result["intent"] == "clarification"
    assert "缺少品項金額" in result["response_markdown"]
    assert memory.snapshot()["events"] == []


def test_agent_handles_looser_receipt_format_with_fallback(tmp_path):
    memory = MemoryStore(tmp_path / "memory.json")
    agent = RoomiePeaceAgent(memory)

    result = agent.handle("今天阿明先墊了公共用品，衛生紙129元，洗衣精159元，垃圾袋65元，餅乾89是他自己的，幫大家算一下")

    assert result["trace"]["intent"] == "receipt_splitter"
    assert result["trace"]["nlu_result"]["source"] == "deterministic_fallback"
    assert "公費總額**：353 元" in result["response_markdown"]
    assert len(memory.snapshot()["events"]) == 1
