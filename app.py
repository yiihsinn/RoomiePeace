"""Streamlit UI for RoomiePeace Superpowers."""

from __future__ import annotations

import streamlit as st

from roomiepeace import MemoryStore, RoomiePeaceAgent
from roomiepeace.tools.karma_tools import build_karma_ranking, calculate_garbage_disaster_index


DEMO_PROMPTS = {
    "建立室友資料": "我們有四個室友：阿明、小美、冠宇、庭萱。小美這週期中考，阿明週三晚上不在，冠宇常常忘記倒垃圾。",
    "分帳 demo": "阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65，幫我們分帳。",
    "家事排班 demo": "幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。",
    "衝突調解 demo": "冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。",
    "室友法庭 demo": "啟動室友法庭，幫我判決冠宇不倒垃圾。",
    "LINE 群組公告": "幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。",
    "Karma 排行榜": "產生本週 Karma 排行榜。",
}


def get_memory() -> MemoryStore:
    if "memory_store" not in st.session_state:
        st.session_state.memory_store = MemoryStore()
    return st.session_state.memory_store


def run_agent(prompt: str) -> None:
    memory = get_memory()
    agent = RoomiePeaceAgent(memory)
    result = agent.handle(prompt)
    st.session_state.latest_result = result
    st.session_state.history.append({"prompt": prompt, "result": result})


def render_sidebar(memory: MemoryStore) -> None:
    snapshot = memory.snapshot()
    st.sidebar.title("RoomiePeace")
    st.sidebar.caption("共居生活 Dashboard")

    if st.sidebar.button("重置 demo memory", use_container_width=True):
        memory.reset()
        st.session_state.history = []
        st.session_state.latest_result = None
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
            st.sidebar.write(f"- {transfer['from']} → {transfer['to']}：{transfer['amount']} 元")
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


def render_result(result: dict) -> None:
    st.markdown(result["response_markdown"])

    tables = result.get("tables", {})
    for title, rows in tables.items():
        if rows:
            st.subheader(title)
            st.dataframe(rows, use_container_width=True, hide_index=True)

    if result.get("line_message"):
        st.subheader("可貼到 LINE 群組的訊息")
        st.text_area(
            "LINE message",
            value=result["line_message"],
            height=180,
            label_visibility="collapsed",
        )


def render_trace(result: dict | None) -> None:
    st.subheader("Agent Trace")
    if not result:
        st.info("先點 quick prompt 或輸入一句話，就會看到 router、skill、tool 和 memory trace。")
        return
    st.json(result.get("trace", {}))

    with st.expander("Memory snapshot", expanded=False):
        st.json(result.get("memory_snapshot", {}))


def main() -> None:
    st.set_page_config(
        page_title="RoomiePeace Superpowers",
        page_icon="RP",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; }
        div[data-testid="stMetricValue"] { font-size: 1.4rem; }
        .stButton > button { border-radius: 8px; height: 2.5rem; }
        textarea { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "history" not in st.session_state:
        st.session_state.history = []
    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None

    memory = get_memory()
    render_sidebar(memory)

    st.title("RoomiePeace Superpowers")
    st.caption("讓 AI Agent 幫室友處理分帳、家事、衝突和搞笑判決")

    st.write("Demo quick prompts")
    prompt_cols = st.columns(4)
    for index, (label, prompt) in enumerate(DEMO_PROMPTS.items()):
        with prompt_cols[index % 4]:
            if st.button(label, use_container_width=True):
                run_agent(prompt)
                st.rerun()

    left, right = st.columns([0.64, 0.36], gap="large")

    with left:
        st.subheader("輸入")
        typed_prompt = st.chat_input("例如：阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65，幫我們分帳。")
        if typed_prompt:
            run_agent(typed_prompt)
            st.rerun()

        result = st.session_state.latest_result
        if result:
            st.subheader("AI Agent 回覆")
            render_result(result)
        else:
            st.info("從上方 quick prompts 開始「冠宇與垃圾桶事件」，或直接輸入任務。")

        if st.session_state.history:
            with st.expander("本次 demo 歷史", expanded=False):
                for item in reversed(st.session_state.history[-6:]):
                    st.markdown(f"**User**：{item['prompt']}")
                    st.markdown(f"**Skill**：{item['result'].get('skill')}")

    with right:
        render_trace(st.session_state.latest_result)


if __name__ == "__main__":
    main()
