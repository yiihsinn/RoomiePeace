"""Streamlit UI for RoomiePeace Superpowers."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from roomiepeace import MemoryStore, RoomiePeaceAgent
from roomiepeace.demo_scenarios import load_demo_scenario
from roomiepeace.tools.karma_tools import build_karma_ranking, calculate_garbage_disaster_index


SKILL_SANDBOX: dict[str, dict[str, Any]] = {
    "receipt_splitter": {
        "skill_name": "receipt-splitter-skill",
        "owner": "A：Receipt Splitter Skill",
        "main_file": "roomiepeace/superpowers/receipt_splitter.py",
        "related_tools": ["roomiepeace/tools/bill_tools.py", "tests/test_bill_tools.py"],
        "default_prompt": "今天阿明先幫大家墊了公共用品，衛生紙129元、洗衣精159元、垃圾袋65元，另外餅乾89元是他自己買來快樂的，幫我們分帳並算誰要轉多少。",
    },
    "chore_planner": {
        "skill_name": "chore-planner-skill",
        "owner": "B：Chore Planner Skill",
        "main_file": "roomiepeace/superpowers/chore_planner.py",
        "related_tools": ["roomiepeace/tools/chore_tools.py"],
        "default_prompt": "幫我們排這週家事。小美這週期中考，阿明週三不在，冠宇上週沒倒垃圾。",
    },
    "conflict_mediator": {
        "skill_name": "conflict-mediator-skill",
        "owner": "C：Conflict Mediator Skill",
        "main_file": "roomiepeace/superpowers/conflict_mediator.py",
        "related_tools": ["roomiepeace/tools/text_tools.py", "roomiepeace/guardrails.py"],
        "default_prompt": "冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。",
    },
    "roomie_court": {
        "skill_name": "roomie-court-skill",
        "owner": "D：Roomie Court Skill",
        "main_file": "roomiepeace/superpowers/roomie_court.py",
        "related_tools": ["roomiepeace/tools/text_tools.py"],
        "default_prompt": "啟動室友法庭，幫我判決冠宇不倒垃圾。",
    },
    "karma_report": {
        "skill_name": "karma-report-skill",
        "owner": "E：Karma Report Skill",
        "main_file": "roomiepeace/superpowers/karma_report.py",
        "related_tools": ["roomiepeace/tools/karma_tools.py"],
        "default_prompt": "產生本週 Karma 排行榜。",
    },
    "line_announcement": {
        "skill_name": "line-announcement-skill",
        "owner": "G / H：Integration Demo Skill",
        "main_file": "roomiepeace/superpowers/line_announcement.py",
        "related_tools": ["roomiepeace/tools/karma_tools.py", "roomiepeace/tools/text_tools.py"],
        "default_prompt": "幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。",
    },
}


TEAM_ROLES = [
    {
        "role": "A",
        "owner": "Receipt Splitter Skill",
        "files": [
            "roomiepeace/superpowers/receipt_splitter.py",
            "roomiepeace/tools/bill_tools.py",
            "tests/test_bill_tools.py",
        ],
        "deliverable": "分帳解析、品項分類、金額計算與分帳測試。",
    },
    {
        "role": "B",
        "owner": "Chore Planner Skill",
        "files": [
            "roomiepeace/superpowers/chore_planner.py",
            "roomiepeace/tools/chore_tools.py",
        ],
        "deliverable": "家事排班邏輯、difficulty 分數與公平性說明。",
    },
    {
        "role": "C",
        "owner": "Conflict Mediator Skill",
        "files": [
            "roomiepeace/superpowers/conflict_mediator.py",
            "roomiepeace/tools/text_tools.py",
            "roomiepeace/guardrails.py",
        ],
        "deliverable": "三種提醒版本、語氣風險與安全降級規則。",
    },
    {
        "role": "D",
        "owner": "Roomie Court Skill",
        "files": [
            "roomiepeace/superpowers/roomie_court.py",
            "roomiepeace/tools/text_tools.py",
        ],
        "deliverable": "娛樂法庭格式、證據、判決理由與免責聲明。",
    },
    {
        "role": "E",
        "owner": "Karma Report Skill",
        "files": [
            "roomiepeace/superpowers/karma_report.py",
            "roomiepeace/tools/karma_tools.py",
        ],
        "deliverable": "Karma 計分、排行榜、稱號與共居狀態。",
    },
    {
        "role": "F",
        "owner": "UI / Dashboard",
        "files": [
            "app.py",
            "docs/demo_script.md",
        ],
        "deliverable": "Guided Demo、Skill Sandbox、Dashboard 和展示畫面整理。",
    },
    {
        "role": "G",
        "owner": "Integration / Router / Memory / Trace",
        "files": [
            "roomiepeace/agent.py",
            "roomiepeace/router.py",
            "roomiepeace/memory.py",
            "roomiepeace/trace.py",
            "data/memory.json",
        ],
        "deliverable": "Router 命中、agent flow、event memory、trace 與整合測試。",
    },
    {
        "role": "H",
        "owner": "Demo / PPT / Video / Evaluation",
        "files": [
            "docs/demo_script.md",
            "docs/project_overview.md",
            "README.md",
            "docs/evaluation_plan.md",
        ],
        "deliverable": "demo 講稿、PPT 素材、錄影順序與評測方式。",
    },
]


BRANCH_NAMES = [
    "feature/receipt-splitter",
    "feature/chore-planner",
    "feature/conflict-mediator",
    "feature/roomie-court",
    "feature/karma-report",
    "feature/ui-guided-demo",
    "feature/integration-router-memory",
    "feature/docs-demo-video",
]


DO_NOT_TOUCH_TOGETHER = [
    "app.py",
    "roomiepeace/agent.py",
    "roomiepeace/router.py",
    "roomiepeace/memory.py",
    "data/memory.json",
    "README.md",
]


PR_CHECKLIST = [
    "`python -m pytest -q` 通過",
    "Streamlit app 可以啟動",
    "在 Skill Sandbox 用 default prompt 測過自己的 skill",
    "再用 custom prompt 測過 router 是否仍命中自己的 skill",
    "Agent Trace 有顯示正確 intent、skill、tools 和 memory updates",
    "沒有 commit `.env`、cache、截圖暫存或 demo runtime memory drift",
]


SKILL_OUTPUT_CONTRACT = """{
    "intent": "...",
    "skill": "...",
    "response_markdown": "...",
    "line_message": "...",
    "tables": {...},
    "tools_used": [...],
    "memory_updates": [...]
}"""


def init_session_state() -> None:
    defaults = {
        "history": [],
        "demo_history": [],
        "demo_results": {},
        "sandbox_results": {},
        "latest_result": None,
        "sandbox_result": None,
        "demo_transcript": "",
        "guided_step_id": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value


def get_memory() -> MemoryStore:
    if "memory_store" not in st.session_state:
        st.session_state.memory_store = MemoryStore()
    return st.session_state.memory_store


def reset_memory_state() -> None:
    memory = get_memory()
    memory.reset()
    st.session_state.history = []
    st.session_state.demo_history = []
    st.session_state.demo_results = {}
    st.session_state.sandbox_results = {}
    st.session_state.latest_result = None
    st.session_state.sandbox_result = None
    st.session_state.demo_transcript = ""
    st.session_state.guided_step_id = ""


def run_agent(prompt: str, source: str, title: str = "") -> dict[str, Any]:
    memory = get_memory()
    agent = RoomiePeaceAgent(memory)
    result = agent.handle(prompt)
    record = {"source": source, "title": title, "prompt": prompt, "result": result}
    st.session_state.latest_result = result
    st.session_state.history.append(record)
    return result


def run_demo_step(step: dict[str, str]) -> dict[str, Any]:
    result = run_agent(step["prompt"], source="guided_demo", title=step["title"])
    st.session_state.demo_results[step["id"]] = result
    st.session_state.demo_history.append({"step": step, "result": result})
    st.session_state.guided_step_id = step["id"]
    return result


def run_full_demo(steps: list[dict[str, str]]) -> None:
    reset_memory_state()
    for step in steps:
        run_demo_step(step)
    st.session_state.guided_step_id = steps[-1]["id"]
    st.session_state.demo_transcript = build_demo_transcript()


def render_sidebar(memory: MemoryStore) -> None:
    snapshot = memory.snapshot()
    st.sidebar.title("RoomiePeace")
    st.sidebar.caption("共居生活 Dashboard")

    if st.sidebar.button("重置 demo memory", use_container_width=True):
        reset_memory_state()
        st.rerun()

    st.sidebar.subheader("室友名單")
    for roommate in snapshot["roommates"]:
        status = snapshot.get("constraints", {}).get(roommate, "無特殊限制")
        st.sidebar.write(f"**{roommate}**：{status}")

    st.sidebar.subheader("公用品庫存")
    for item, status in snapshot.get("inventory", {}).items():
        st.sidebar.write(f"- {item}：{status}")

    st.sidebar.subheader("未結清款項")
    latest_expense = snapshot.get("expenses", [])[-1:] or []
    if latest_expense:
        for transfer in latest_expense[0].get("transfers", []):
            st.sidebar.write(f"- {transfer['from']} -> {transfer['to']}：{transfer['amount']} 元")
    else:
        st.sidebar.write("目前沒有新的分帳。")

    disaster_index = calculate_garbage_disaster_index(snapshot)
    st.sidebar.subheader("Garbage Disaster Index")
    st.sidebar.progress(disaster_index / 100)
    st.sidebar.write(f"{disaster_index} / 100")

    st.sidebar.subheader("Karma 排行榜")
    for index, row in enumerate(build_karma_ranking(snapshot), start=1):
        st.sidebar.write(f"{index}. {row['roommate']}：{row['score']} 分")

    st.sidebar.subheader("家事完成紀錄")
    latest_chore = snapshot.get("chores", [])[-1:] or []
    if latest_chore:
        for assignment in latest_chore[0].get("assignments", []):
            st.sidebar.write(f"- {assignment['assignee']}：{assignment['task']}")
    else:
        st.sidebar.write("尚未排班。")


def render_tables(result: dict[str, Any]) -> None:
    tables = result.get("tables", {})
    for title, rows in tables.items():
        if rows:
            st.markdown(f"**{title}**")
            st.dataframe(rows, use_container_width=True, hide_index=True)


def render_line_message(result: dict[str, Any], key: str) -> None:
    line_message = result.get("line_message", "")
    if not line_message:
        return
    st.markdown("**LINE message**")
    st.text_area(
        "LINE message",
        value=line_message,
        height=160,
        label_visibility="collapsed",
        key=key,
    )


def render_memory_updates(result: dict[str, Any]) -> None:
    updates = result.get("trace", {}).get("memory_updates") or result.get("memory_updates", [])
    if not updates:
        st.write("無 memory update。")
        return
    for update in updates:
        st.write(f"- {update}")


def render_result(result: dict[str, Any], key_prefix: str) -> None:
    render_roomie_court_memory_evidence(result)
    st.markdown(result["response_markdown"])
    render_tables(result)
    render_line_message(result, key=f"{key_prefix}_line_message")


def render_trace(result: dict[str, Any] | None, expanded: bool = True) -> None:
    if not result:
        st.info("還沒有執行結果。")
        return
    trace = result.get("trace", {})
    st.json(trace, expanded=expanded)


def get_completed_demo_count(steps: list[dict[str, str]]) -> int:
    return sum(1 for step in steps if step["id"] in st.session_state.demo_results)


def get_current_demo_step(steps: list[dict[str, str]]) -> tuple[int, dict[str, str]]:
    if not st.session_state.guided_step_id:
        st.session_state.guided_step_id = steps[0]["id"]
    for index, step in enumerate(steps, start=1):
        if step["id"] == st.session_state.guided_step_id:
            return index, step
    st.session_state.guided_step_id = steps[0]["id"]
    return 1, steps[0]


def get_next_pending_step(steps: list[dict[str, str]]) -> dict[str, str]:
    for step in steps:
        if step["id"] not in st.session_state.demo_results:
            return step
    return steps[-1]


def route_status(result: dict[str, Any] | None, step: dict[str, str]) -> tuple[str, str]:
    if not result:
        return "Ready", "neutral"
    trace = result.get("trace", {})
    matched = (
        trace.get("intent") == step["expected_intent"]
        and trace.get("selected_superpower") == step["expected_skill"]
    )
    if matched and trace.get("guardrail_result", {}).get("safe"):
        return "Matched", "ok"
    if matched:
        return "Guardrail check", "warn"
    return "Check routing", "warn"


def status_chip(label: str, tone: str = "neutral") -> str:
    return f"<span class='rp-chip rp-chip-{tone}'>{escape(label)}</span>"


def display_value(value: Any, fallback: str = "—") -> str:
    if value is None or value == "" or value == []:
        return fallback
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def short_list(values: list[Any], limit: int = 3) -> str:
    if not values:
        return "none"
    visible = [str(value) for value in values[:limit]]
    suffix = f" +{len(values) - limit}" if len(values) > limit else ""
    return ", ".join(visible) + suffix


def nlu_source_label(source: str) -> tuple[str, str]:
    if source == "vertex_gemini_structured_output":
        return "Vertex Gemini", "ai"
    if "fallback" in source:
        return "Deterministic fallback", "warn"
    return display_value(source), "neutral"


def render_pipeline_trace(result: dict[str, Any] | None) -> None:
    if not result:
        st.info("還沒有 pipeline trace。")
        return

    trace = result.get("trace", {})
    nlu = trace.get("nlu_result", {})
    nlu_label, nlu_tone = nlu_source_label(nlu.get("source", ""))
    guardrail = trace.get("guardrail_result", {})
    tools = trace.get("tools_used", [])
    memory_updates = trace.get("memory_updates", [])
    guardrail_safe = guardrail.get("safe")

    nodes = [
        ("01", "User Input", "自然語言需求", "rp-flow-node-neutral"),
        ("02", "NLU", nlu_label, f"rp-flow-node-{nlu_tone}"),
        ("03", "Router", trace.get("intent", result.get("intent", "unknown")), "rp-flow-node-neutral"),
        ("04", "Skill", trace.get("selected_superpower", result.get("skill", "unknown")), "rp-flow-node-skill"),
        ("05", "Tools", short_list(tools), "rp-flow-node-tool"),
        ("06", "Memory", f"{len(memory_updates)} updates", "rp-flow-node-memory"),
        ("07", "Guardrail", "safe" if guardrail_safe else "check", "rp-flow-node-safe" if guardrail_safe else "rp-flow-node-warn"),
        ("08", "Output", "LINE / tables / markdown", "rp-flow-node-output"),
    ]
    cards = []
    for number, label, value, class_name in nodes:
        cards.append(
            f"""
            <div class="rp-flow-node {class_name}">
              <div class="rp-flow-number">{escape(number)}</div>
              <div class="rp-flow-label">{escape(label)}</div>
              <div class="rp-flow-value">{escape(display_value(value))}</div>
            </div>
            """
        )
    st.markdown(f"<div class='rp-pipeline'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_nlu_summary(result: dict[str, Any] | None) -> None:
    if not result:
        st.info("還沒有 NLU summary。")
        return

    trace = result.get("trace", {})
    nlu = trace.get("nlu_result", {})
    data = nlu.get("data", {}) or {}
    nlu_label, nlu_tone = nlu_source_label(nlu.get("source", ""))
    confidence = nlu.get("confidence")
    actor = data.get("payer") or data.get("target") or "—"
    topic = data.get("topic") or ("分帳" if nlu.get("intent") == "receipt_splitter" else "—")
    cards = [
        ("NLU source", status_chip(nlu_label, nlu_tone)),
        ("Intent", f"<code>{escape(display_value(nlu.get('intent')))}</code>"),
        ("Confidence", escape(display_value(confidence))),
        ("Actor / target", escape(display_value(actor))),
        ("Topic", escape(display_value(topic))),
        ("Tone", escape(display_value(data.get("tone", "funny but polite")))),
    ]
    rendered_cards = []
    for label, value in cards:
        rendered_cards.append(
            f"""
            <div class="rp-insight-card">
              <div class="rp-insight-label">{escape(label)}</div>
              <div class="rp-insight-value">{value}</div>
            </div>
            """
        )
    st.markdown(f"<div class='rp-insight-grid'>{''.join(rendered_cards)}</div>", unsafe_allow_html=True)

    missing_fields = nlu.get("missing_fields", [])
    if missing_fields:
        st.warning(f"需要補充欄位：{', '.join(missing_fields)}")

    items = data.get("items", []) or []
    if items:
        st.markdown("**Extracted receipt items**")
        item_rows = [
            {
                "品項": item.get("name"),
                "金額": item.get("amount"),
                "NLU 分類": {
                    "shared": "公用品",
                    "personal": "個人物品",
                    "unknown": "待判斷",
                }.get(item.get("classification"), item.get("classification")),
            }
            for item in items
        ]
        st.dataframe(item_rows, use_container_width=True, hide_index=True)

    notes = nlu.get("notes")
    if notes:
        st.caption(notes)


def render_roomie_court_memory_evidence(result: dict[str, Any]) -> None:
    if result.get("skill") != "roomie-court-skill":
        return
    prior_records = result.get("tables", {}).get("累犯紀錄", [])
    if not prior_records:
        return

    evidence_cards = []
    for index, record in enumerate(prior_records, start=1):
        evidence_cards.append(
            f"""
            <div class="rp-evidence-card">
              <div class="rp-evidence-index">{index}</div>
              <div>
                <div class="rp-evidence-type">{escape(display_value(record.get('類型')))}</div>
                <div class="rp-evidence-text">{escape(display_value(record.get('內容')))}</div>
              </div>
            </div>
            """
        )
    st.markdown("**累犯依據：Memory 讀到的前情提要**")
    st.markdown(f"<div class='rp-evidence-grid'>{''.join(evidence_cards)}</div>", unsafe_allow_html=True)


def render_demo_metrics(steps: list[dict[str, str]]) -> None:
    memory = get_memory()
    snapshot = memory.snapshot()
    completed = get_completed_demo_count(steps)
    latest_trace = (st.session_state.latest_result or {}).get("trace", {})
    metric_cols = st.columns(4)
    metric_cols[0].metric("Progress", f"{completed}/{len(steps)}")
    metric_cols[1].metric("Memory events", len(snapshot.get("events", [])))
    metric_cols[2].metric("Garbage index", calculate_garbage_disaster_index(snapshot))
    metric_cols[3].metric("Latest skill", latest_trace.get("selected_superpower", "none"))


def render_demo_step_rail(steps: list[dict[str, str]], current_step_id: str) -> None:
    for index, step in enumerate(steps, start=1):
        result = st.session_state.demo_results.get(step["id"])
        status, tone = route_status(result, step)
        button_label = f"{index}. {step['title']}"
        if st.button(button_label, key=f"select_step_{step['id']}", use_container_width=True):
            st.session_state.guided_step_id = step["id"]
            st.rerun()
        current_class = " rp-step-current" if step["id"] == current_step_id else ""
        st.markdown(
            f"""
            <div class="rp-step-card{current_class}">
              <div class="rp-step-row">
                <strong>{index}</strong>
                {status_chip(status, tone)}
              </div>
              <div class="rp-step-title">{step['title']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_selected_demo_step(index: int, step: dict[str, str]) -> None:
    result = st.session_state.demo_results.get(step["id"])
    status, tone = route_status(result, step)

    st.markdown(
        f"""
        <div class="rp-demo-stage">
          <div class="rp-stage-kicker">Step {index}</div>
          <h3>{step['title']}</h3>
          <p>{step['purpose']}</p>
          {status_chip(status, tone)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    target_cols = st.columns(2)
    with target_cols[0]:
        st.markdown("**Expected intent**")
        st.code(step["expected_intent"], language="text")
    with target_cols[1]:
        st.markdown("**Expected skill**")
        st.code(step["expected_skill"], language="text")

    st.markdown("**Prompt**")
    st.code(step["prompt"], language="text")

    run_cols = st.columns([1, 3])
    with run_cols[0]:
        if st.button("Run this step", type="primary", key=f"run_current_{step['id']}", use_container_width=True):
            result = run_demo_step(step)
            st.session_state.demo_transcript = ""

    if not result:
        st.info("這一步還沒跑。上台 demo 時先確認 prompt，再按 Run this step。")
        return

    trace = result.get("trace", {})
    actual_cols = st.columns(3)
    actual_cols[0].metric("Actual intent", trace.get("intent", "unknown"))
    actual_cols[1].metric("Actual skill", trace.get("selected_superpower", "unknown"))
    actual_cols[2].metric("Memory updates", len(trace.get("memory_updates", [])))

    st.markdown("**Agent Pipeline**")
    render_pipeline_trace(result)
    with st.expander("NLU extraction summary", expanded=True):
        render_nlu_summary(result)

    output_col, trace_col = st.columns([0.62, 0.38], gap="large")
    with output_col:
        st.subheader("Output")
        render_result(result, key_prefix=f"demo_focus_{step['id']}")
    with trace_col:
        st.subheader("Trace")
        st.markdown("**Memory updates**")
        render_memory_updates(result)
        st.markdown("**Agent Trace**")
        render_trace(result, expanded=False)


def build_demo_transcript() -> str:
    lines = ["# RoomiePeace Demo Transcript", ""]
    for index, item in enumerate(st.session_state.demo_history, start=1):
        step = item["step"]
        result = item["result"]
        trace = result.get("trace", {})
        lines.extend(
            [
                f"## Step {index}: {step['title']}",
                "",
                f"Purpose: {step['purpose']}",
                "",
                f"Prompt: {step['prompt']}",
                "",
                f"Expected intent: `{step['expected_intent']}`",
                f"Actual intent: `{trace.get('intent', result.get('intent'))}`",
                f"Expected skill: `{step['expected_skill']}`",
                f"Actual skill: `{trace.get('selected_superpower', result.get('skill'))}`",
                "",
                "Memory updates:",
            ]
        )
        updates = trace.get("memory_updates", [])
        lines.extend([f"- {update}" for update in updates] or ["- None"])
        if result.get("line_message"):
            lines.extend(["", "LINE message:", "", "```text", result["line_message"], "```"])
        lines.extend(["", "Output:", "", result.get("response_markdown", ""), ""])
    return "\n".join(lines)


def render_demo_summary() -> None:
    if not st.session_state.demo_history:
        st.info("尚未執行 demo。可以逐步跑，也可以直接 Run full demo。")
        return
    rows = []
    for index, item in enumerate(st.session_state.demo_history, start=1):
        step = item["step"]
        result = item["result"]
        trace = result.get("trace", {})
        rows.append(
            {
                "Step": index,
                "Title": step["title"],
                "Expected intent": step["expected_intent"],
                "Actual intent": trace.get("intent"),
                "Expected skill": step["expected_skill"],
                "Actual skill": trace.get("selected_superpower"),
                "Memory updates": len(trace.get("memory_updates", [])),
                "Safe": trace.get("guardrail_result", {}).get("safe"),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_guided_demo_tab() -> None:
    scenario = load_demo_scenario()
    steps = scenario["steps"]
    current_index, current_step = get_current_demo_step(steps)
    completed = get_completed_demo_count(steps)

    st.header("Guided Demo")
    st.caption(f"故事線：{scenario['scenario_name']}")
    st.progress(completed / len(steps))
    render_demo_metrics(steps)

    control_cols = st.columns([1, 1, 1, 1.25])
    with control_cols[0]:
        if st.button("Reset demo memory", use_container_width=True):
            reset_memory_state()
            st.rerun()
    with control_cols[1]:
        if st.button("Run current step", type="primary", use_container_width=True):
            run_demo_step(current_step)
            st.session_state.demo_transcript = ""
            st.rerun()
    with control_cols[2]:
        if st.button("Run full demo", type="primary", use_container_width=True):
            run_full_demo(steps)
            st.rerun()
    with control_cols[3]:
        if st.button("Export demo transcript", use_container_width=True):
            st.session_state.demo_transcript = build_demo_transcript()

    next_step = get_next_pending_step(steps)
    st.markdown(
        f"""
        <div class="rp-demo-note">
          <strong>Now:</strong> Step {current_index} · {current_step['title']}
          <span>Next pending: {next_step['title']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step_col, stage_col = st.columns([0.26, 0.74], gap="large")
    with step_col:
        st.subheader("Steps")
        render_demo_step_rail(steps, current_step["id"])
    with stage_col:
        render_selected_demo_step(current_index, current_step)

    st.subheader("Demo Summary")
    render_demo_summary()

    if st.session_state.demo_transcript:
        st.text_area(
            "Demo transcript markdown",
            value=st.session_state.demo_transcript,
            height=300,
        )


def render_skill_sandbox_tab() -> None:
    st.header("Skill Sandbox")
    st.caption("給 skill owners 單獨測自己的 prompt、router 命中、output contract 和 memory updates。")

    selected_skill = st.selectbox("Select skill", list(SKILL_SANDBOX.keys()))
    config = SKILL_SANDBOX[selected_skill]

    info_cols = st.columns([1, 1])
    with info_cols[0]:
        st.markdown(f"**Skill name**：`{config['skill_name']}`")
        st.markdown(f"**Owner role**：{config['owner']}")
        st.markdown(f"**Main file**：`{config['main_file']}`")
    with info_cols[1]:
        st.markdown("**Related tools**")
        for file_path in config["related_tools"]:
            st.write(f"- `{file_path}`")

    st.markdown("**Default test prompt**")
    st.code(config["default_prompt"], language="text")

    custom_prompt = st.text_area(
        "Custom prompt",
        value=config["default_prompt"],
        height=120,
        key=f"sandbox_prompt_{selected_skill}",
    )
    reset_before_run = st.checkbox("Reset memory before run", value=False)

    if st.button("Run through Agent", type="primary"):
        if reset_before_run:
            reset_memory_state()
        result = run_agent(custom_prompt, source="skill_sandbox", title=selected_skill)
        st.session_state.sandbox_result = result
        st.session_state.sandbox_results[selected_skill] = result

    result = st.session_state.sandbox_results.get(selected_skill)
    if result:
        trace = result.get("trace", {})
        route_cols = st.columns(2)
        route_cols[0].metric("Router intent", trace.get("intent", result.get("intent", "unknown")))
        route_cols[1].metric("Selected skill", trace.get("selected_superpower", result.get("skill", "unknown")))

        st.subheader("Agent Pipeline")
        render_pipeline_trace(result)
        with st.expander("NLU extraction summary", expanded=True):
            render_nlu_summary(result)

        st.subheader("Output result")
        render_result(result, key_prefix=f"sandbox_{selected_skill}")
        st.subheader("Trace")
        render_trace(result, expanded=True)
        st.subheader("Memory snapshot")
        st.json(result.get("memory_snapshot", {}), expanded=False)
    else:
        st.info("選 skill 後可以先用 default prompt 跑一次，再改 custom prompt 測 router 命中。")


def render_collaboration_dashboard_tab() -> None:
    st.header("Collaboration Dashboard")
    st.caption("八人分工、branch 規範、PR checklist 和 skill output contract 集中在這裡。")

    role_rows = []
    for role in TEAM_ROLES:
        role_rows.append(
            {
                "Role": role["role"],
                "Owner": role["owner"],
                "Main files": "\n".join(role["files"]),
                "Deliverable": role["deliverable"],
            }
        )
    st.dataframe(role_rows, use_container_width=True, hide_index=True, height=430)

    left, right = st.columns(2)
    with left:
        st.subheader("Branch naming convention")
        st.code("\n".join(BRANCH_NAMES), language="text")

        st.subheader("不要互相踩的檔案")
        for file_path in DO_NOT_TOUCH_TOGETHER:
            st.write(f"- `{file_path}`")

    with right:
        st.subheader("PR checklist")
        for item in PR_CHECKLIST:
            st.checkbox(item, value=False, disabled=True)

        st.subheader("Skill output contract")
        st.code(SKILL_OUTPUT_CONTRACT, language="python")

    st.subheader("開發建議")
    st.write("- Skill owner 主要改自己的 `superpowers/` 和 `tools/` 檔案。")
    st.write("- Merge 前先到 Skill Sandbox 跑 default prompt 和 custom prompt。")
    st.write("- F / G 需要改整合層時，先跟 skill owners 對齊避免同時改同一段 UI 或 router。")
    st.write("- H 可以修改 `data/demo_scenarios.json` 調整 demo 文案，不需要改 `app.py`。")


def main() -> None:
    st.set_page_config(
        page_title="RoomiePeace Superpowers",
        page_icon="RP",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; }
        div[data-testid="stMetricValue"] { font-size: 1rem; }
        div[data-testid="stMetric"] {
          padding: 0.72rem 0.82rem;
          border: 1px solid #e0e6ef;
          border-radius: 8px;
          background: #ffffff;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }
        div[data-testid="stMetric"]:hover {
          transform: translateY(-2px);
          border-color: #9eb1d9;
          box-shadow: 0 10px 26px rgba(32, 43, 70, 0.09);
        }
        .stButton > button {
          border-radius: 8px;
          min-height: 2.4rem;
          transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
        }
        .stButton > button:hover {
          transform: translateY(-1px);
          box-shadow: 0 8px 18px rgba(33, 49, 90, 0.12);
          border-color: #5b77d6;
        }
        .stButton > button:active {
          transform: translateY(0);
        }
        textarea { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        textarea:focus {
          border-color: #5b77d6 !important;
          box-shadow: 0 0 0 2px rgba(91, 119, 214, 0.14) !important;
        }
        code { white-space: pre-wrap; }
        .rp-chip {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 0.16rem 0.55rem;
          font-size: 0.76rem;
          font-weight: 700;
          border: 1px solid #d7dde8;
          color: #42526b;
          background: #f8fafc;
        }
        .rp-chip-ok {
          border-color: #9fd3b8;
          color: #17643b;
          background: #ecfdf3;
        }
        .rp-chip-warn {
          border-color: #f2c77b;
          color: #8a4b05;
          background: #fff7e6;
        }
        .rp-chip-ai {
          border-color: #85c8c2;
          color: #075e59;
          background: #eafaf8;
        }
        .rp-demo-note {
          display: flex;
          gap: 1rem;
          justify-content: space-between;
          align-items: center;
          margin: 0.8rem 0 1rem;
          padding: 0.75rem 0.9rem;
          border: 1px solid #d9e2ef;
          border-radius: 8px;
          background: #fbfcfe;
          color: #25324a;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }
        .rp-demo-note:hover {
          transform: translateY(-1px);
          border-color: #aab9d6;
          box-shadow: 0 9px 24px rgba(32, 43, 70, 0.08);
        }
        .rp-step-card {
          margin: 0.35rem 0 0.85rem;
          padding: 0.7rem 0.75rem;
          border: 1px solid #dce3ee;
          border-radius: 8px;
          background: #ffffff;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease;
          cursor: default;
        }
        .rp-step-card:hover {
          transform: translateX(3px);
          border-color: #9eb1d9;
          background: #fbfcff;
          box-shadow: 0 8px 22px rgba(32, 43, 70, 0.08);
        }
        .rp-step-current {
          border-color: #4466d8;
          box-shadow: 0 0 0 1px rgba(68, 102, 216, 0.12);
        }
        .rp-step-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.35rem;
        }
        .rp-step-title {
          color: #25324a;
          font-weight: 650;
          line-height: 1.35;
        }
        .rp-demo-stage {
          margin-bottom: 1rem;
          padding: 1rem 1.1rem;
          border: 1px solid #d9e2ef;
          border-radius: 8px;
          background: #ffffff;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }
        .rp-demo-stage:hover {
          transform: translateY(-2px);
          border-color: #9eb1d9;
          box-shadow: 0 12px 30px rgba(32, 43, 70, 0.08);
        }
        .rp-demo-stage h3 {
          margin: 0.1rem 0 0.4rem;
          font-size: 1.35rem;
        }
        .rp-demo-stage p {
          margin: 0 0 0.75rem;
          color: #53627a;
        }
        .rp-stage-kicker {
          color: #4466d8;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0;
        }
        .rp-pipeline {
          display: grid;
          grid-template-columns: repeat(8, minmax(0, 1fr));
          gap: 0.55rem;
          margin: 0.45rem 0 1rem;
        }
        .rp-flow-node {
          min-height: 6.3rem;
          padding: 0.68rem 0.62rem;
          border: 1px solid #dfe6f0;
          border-radius: 8px;
          background: #ffffff;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
          overflow: hidden;
        }
        .rp-flow-node:hover {
          transform: translateY(-3px);
          box-shadow: 0 12px 28px rgba(32, 43, 70, 0.11);
          border-color: #8fa2cc;
        }
        .rp-flow-number {
          display: inline-flex;
          width: 1.45rem;
          height: 1.45rem;
          align-items: center;
          justify-content: center;
          margin-bottom: 0.46rem;
          border-radius: 999px;
          font-size: 0.7rem;
          font-weight: 800;
          color: #ffffff;
          background: #4d607d;
        }
        .rp-flow-label {
          font-size: 0.72rem;
          font-weight: 800;
          color: #56637a;
          text-transform: uppercase;
          letter-spacing: 0;
        }
        .rp-flow-value {
          margin-top: 0.22rem;
          color: #1f2b3d;
          font-weight: 750;
          font-size: 0.82rem;
          line-height: 1.25;
          overflow-wrap: anywhere;
        }
        .rp-flow-node-ai { background: #f0fbfa; border-color: #b7ded9; }
        .rp-flow-node-skill { background: #f6f2ff; border-color: #d3c5f1; }
        .rp-flow-node-tool { background: #fff7ea; border-color: #edcf98; }
        .rp-flow-node-memory { background: #f1f8ef; border-color: #bdd8b5; }
        .rp-flow-node-safe { background: #effaf4; border-color: #afd6be; }
        .rp-flow-node-warn { background: #fff5ed; border-color: #e7bd91; }
        .rp-flow-node-output { background: #eef6ff; border-color: #bad0ea; }
        .rp-insight-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.7rem;
          margin: 0.3rem 0 0.9rem;
        }
        .rp-insight-card {
          padding: 0.78rem 0.82rem;
          border: 1px solid #dfe6f0;
          border-radius: 8px;
          background: #ffffff;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }
        .rp-insight-card:hover {
          transform: translateY(-2px);
          border-color: #9eb1d9;
          box-shadow: 0 10px 24px rgba(32, 43, 70, 0.08);
        }
        .rp-insight-label {
          color: #61708a;
          font-size: 0.74rem;
          font-weight: 750;
          text-transform: uppercase;
          letter-spacing: 0;
        }
        .rp-insight-value {
          margin-top: 0.22rem;
          color: #1f2b3d;
          font-size: 0.96rem;
          font-weight: 750;
          overflow-wrap: anywhere;
        }
        .rp-evidence-grid {
          display: grid;
          gap: 0.55rem;
          margin: 0.35rem 0 0.95rem;
        }
        .rp-evidence-card {
          display: grid;
          grid-template-columns: 2rem minmax(0, 1fr);
          gap: 0.65rem;
          align-items: start;
          padding: 0.72rem 0.78rem;
          border: 1px solid #e1e7ef;
          border-radius: 8px;
          background: #fffdf8;
          transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }
        .rp-evidence-card:hover {
          transform: translateX(3px);
          border-color: #e1bd73;
          box-shadow: 0 10px 24px rgba(83, 68, 37, 0.08);
        }
        .rp-evidence-index {
          width: 1.65rem;
          height: 1.65rem;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          background: #293549;
          color: #ffffff;
          font-weight: 800;
          font-size: 0.78rem;
        }
        .rp-evidence-type {
          color: #8a5a0b;
          font-weight: 800;
          font-size: 0.78rem;
          text-transform: uppercase;
          letter-spacing: 0;
        }
        .rp-evidence-text {
          color: #26364c;
          line-height: 1.42;
          font-weight: 620;
        }
        @media (max-width: 1100px) {
          .rp-pipeline {
            grid-template-columns: repeat(4, minmax(0, 1fr));
          }
          .rp-insight-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }
        @media (max-width: 760px) {
          .rp-demo-note {
            display: block;
          }
          .rp-pipeline,
          .rp-insight-grid {
            grid-template-columns: 1fr;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_session_state()
    memory = get_memory()
    render_sidebar(memory)

    st.title("RoomiePeace Superpowers")
    st.caption("Skill-based 共居生活協調 Agent：Router -> Skill -> Tools -> Memory -> Guardrail -> Trace")

    guided_demo_tab, skill_sandbox_tab, collaboration_tab = st.tabs(
        ["Guided Demo", "Skill Sandbox", "Collaboration Dashboard"]
    )

    with guided_demo_tab:
        render_guided_demo_tab()
    with skill_sandbox_tab:
        render_skill_sandbox_tab()
    with collaboration_tab:
        render_collaboration_dashboard_tab()


if __name__ == "__main__":
    main()
