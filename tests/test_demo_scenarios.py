from roomiepeace.demo_scenarios import (
    DEFAULT_DEMO_SCENARIO,
    load_demo_scenario,
    validate_demo_scenario,
)
from roomiepeace.router import route


def test_demo_scenarios_json_can_be_loaded():
    scenario = load_demo_scenario()

    assert scenario["scenario_name"] == "冠宇與垃圾桶事件"
    assert len(scenario["steps"]) == 7


def test_demo_scenario_steps_have_required_fields():
    scenario = load_demo_scenario()

    for step in scenario["steps"]:
        assert step["prompt"]
        assert step["expected_intent"]
        assert step["expected_skill"]


def test_demo_scenario_expected_routes_match_router():
    scenario = load_demo_scenario()

    for step in scenario["steps"]:
        route_result = route(step["prompt"])
        assert route_result.intent == step["expected_intent"]
        assert route_result.selected_superpower == step["expected_skill"]


def test_demo_scenario_falls_back_when_missing(tmp_path):
    missing_path = tmp_path / "missing_demo_scenarios.json"
    scenario = load_demo_scenario(missing_path)

    assert scenario == DEFAULT_DEMO_SCENARIO
    validate_demo_scenario(scenario)
