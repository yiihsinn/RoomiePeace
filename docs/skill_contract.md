# Skill Contract

這份文件給 A 到 G 使用。每個 skill 可以自由改善內容，但必須維持共同輸出格式，讓 Streamlit UI、Guided Demo、Skill Sandbox、Agent Trace 都能穩定顯示。

## handle 函式格式

每個 skill module 需要提供：

```python
def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    ...
```

輸入：

- `user_input`：使用者原始輸入
- `memory`：`MemoryStore`，用來讀取 snapshot 與寫入事件

輸出：

```python
{
    "intent": "...",
    "skill": "...",
    "response_markdown": "...",
    "line_message": "...",
    "tables": {...},
    "tools_used": [...],
    "memory_updates": [...]
}
```

## 欄位說明

### intent

Router 判斷出的任務類型，例如：

- `receipt_splitter`
- `chore_planner`
- `conflict_mediator`
- `roomie_court`
- `karma_report`
- `line_announcement`

### skill

人類可讀的 skill 名稱，例如：

- `receipt-splitter-skill`
- `chore-planner-skill`
- `conflict-mediator-skill`
- `roomie-court-skill`
- `karma-report-skill`
- `line-announcement-skill`

### response_markdown

主要輸出，使用 Markdown 格式。Guided Demo 和 Skill Sandbox 會直接用 `st.markdown()` 顯示。

注意：

- 可以有趣，但不能霸凌。
- 不要在這裡做精準計算。
- 計算結果應來自 tools。

### line_message

可貼到 LINE 群組的文字。不是每個 skill 都一定要很長，但建議保留，方便 demo。

注意：

- 不串 LINE API。
- 不做真實轉帳。
- 不公開私人個資。
- 群組公告語氣要比私訊保守。

### tables

用於 UI 顯示表格。格式是：

```python
{
    "表格名稱": [
        {"欄位A": "值", "欄位B": 123},
        {"欄位A": "值", "欄位B": 456}
    ]
}
```

範例：

```python
{
    "轉帳建議": [
        {"from": "小美", "to": "阿明", "amount": 88},
        {"from": "冠宇", "to": "阿明", "amount": 88}
    ]
}
```

### tools_used

列出 skill 實際呼叫的工具名稱。Trace 會顯示這個欄位，用來證明不是普通 chatbot。

範例：

```python
["parse_receipt_items", "classify_item", "split_bill"]
```

### memory_updates

列出這次處理更新了哪些 memory。

範例：

```python
[
    "expense_created event @ 2026-05-30T20:30:00",
    "阿明 karma +2",
    "inventory updated: 衛生紙、洗衣精、垃圾袋"
]
```

## Memory 寫入要求

重要生活事件要寫進 memory，不要只出現在 markdown。

推薦 event type：

- `expense_created`
- `chore_assigned`
- `conflict_mediated`
- `court_case_created`
- `line_announcement_created`

請優先使用 `MemoryStore` 已有方法。只有現有方法不足時，再新增 method。

## 新增 skill 時注意事項

新增第六個以上 skill 時，通常需要：

1. 新增 `roomiepeace/superpowers/new_skill.py`
2. 必要時新增 `roomiepeace/tools/new_tools.py`
3. 在 `roomiepeace/router.py` 加 route keywords
4. 在 `roomiepeace/agent.py` 接上 handle
5. 在 `app.py` 的 `SKILL_SANDBOX` 加設定
6. 必要時在 `data/demo_scenarios.json` 加 step
7. 加測試
8. 更新 README 或 demo docs

## Merge 前檢查

- `python -m pytest -q` 通過
- Skill Sandbox default prompt 通過
- Skill Sandbox custom prompt router 命中正確
- Trace 顯示 tools_used 和 memory_updates
- Guardrail safe 或能合理降級
