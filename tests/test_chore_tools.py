from roomiepeace.tools.chore_tools import (
    calculate_fairness_score,
    generate_chore_schedule,
    parse_chore_tasks,
)


ROOMMATES = ["阿明", "小美", "冠宇", "庭萱"]
CONSTRAINTS = {
    "阿明": "週三晚上不在",
    "小美": "本週期中考",
    "冠宇": "常常忘記倒垃圾",
    "庭萱": "無特殊限制",
}


def _assignment_map(schedule):
    return {
        assignment["task"]: assignment["assignee"]
        for assignment in schedule["assignments"]
    }


def test_parse_chore_tasks_uses_only_requested_known_tasks():
    assert parse_chore_tasks("請安排拖地和洗浴室") == [
        {"task": "拖地", "difficulty": 2},
        {"task": "洗浴室", "difficulty": 3},
    ]


def test_parse_chore_tasks_uses_defaults_when_no_known_task_is_given():
    assert [task["task"] for task in parse_chore_tasks("幫我們排這週家事")] == [
        "倒垃圾",
        "補衛生紙",
        "拖地",
        "洗浴室",
    ]


def test_demo_schedule_respects_constraints_and_reports_fairness():
    schedule = generate_chore_schedule(
        "幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。",
        ROOMMATES,
        CONSTRAINTS,
        [],
    )

    assert _assignment_map(schedule) == {
        "倒垃圾": "冠宇",
        "拖地": "阿明",
        "洗浴室": "庭萱",
        "補衛生紙": "小美",
    }
    assert schedule["fairness_score"] == 86


def test_exam_week_roommate_gets_light_task_and_avoids_heavy_task():
    schedule = generate_chore_schedule(
        "幫我們排倒垃圾、拖地、洗浴室、補衛生紙。",
        ["小美", "阿明", "冠宇", "庭萱"],
        {"小美": "本週期中考"},
        [],
    )
    assignments = _assignment_map(schedule)

    assert assignments["補衛生紙"] == "小美"
    assert assignments["洗浴室"] != "小美"
    assert assignments["拖地"] != "小美"


def test_trash_task_is_assigned_to_roommate_with_trash_debt():
    schedule = generate_chore_schedule(
        "請安排倒垃圾。",
        ["怡君", "博文", "冠宇"],
        {"冠宇": "上週忘記倒垃圾"},
        [],
    )

    assert _assignment_map(schedule)["倒垃圾"] == "冠宇"


def test_timely_trash_task_avoids_roommate_who_is_away():
    schedule = generate_chore_schedule(
        "請安排倒垃圾。",
        ["怡君", "博文"],
        {"怡君": "週三晚上不在"},
        [],
    )

    assert _assignment_map(schedule)["倒垃圾"] == "博文"


def test_recently_overloaded_roommate_does_not_receive_heavy_task():
    chore_history = [
        {
            "assignments": [
                {"task": "洗浴室", "assignee": "怡君", "difficulty": 3},
                {"task": "拖地", "assignee": "怡君", "difficulty": 2},
            ]
        }
    ]
    schedule = generate_chore_schedule(
        "請安排洗浴室。",
        ["怡君", "博文", "冠宇"],
        {},
        chore_history,
    )

    assert _assignment_map(schedule)["洗浴室"] == "博文"
    assert schedule["previous_loads"] == {"怡君": 5, "博文": 0, "冠宇": 0}


def test_fairness_score_includes_unassigned_roommates_and_recent_loads():
    balanced = calculate_fairness_score(
        [
            {"task": "倒垃圾", "assignee": "怡君", "difficulty": 1},
            {"task": "補衛生紙", "assignee": "博文", "difficulty": 1},
        ],
        ["怡君", "博文"],
        {},
    )
    imbalanced = calculate_fairness_score(
        [{"task": "洗浴室", "assignee": "怡君", "difficulty": 3}],
        ["怡君", "博文", "冠宇"],
        {"怡君": 2, "博文": 0, "冠宇": 0},
    )

    assert balanced == 100
    assert 0 <= imbalanced < balanced


def test_empty_roommate_list_returns_empty_schedule():
    schedule = generate_chore_schedule("幫我們排家事", [], {}, [])

    assert schedule["assignments"] == []
    assert schedule["fairness_score"] == 100
    assert schedule["loads"] == {}

