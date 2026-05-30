# RoomiePeace 小組分工必讀

這份文件是給五個人同時開發用的。目標很簡單：每個人可以安心負責一個 skill，最後整合時不要互相踩檔案、不要 merge 到懷疑人生。

## 分工總覽

建議五個人各自負責一個 Superpower / Skill：

| 成員 | Skill | 主要檔案 | 搭配工具檔 |
| --- | --- | --- | --- |
| A | 分帳技能 | `roomiepeace/superpowers/receipt_splitter.py` | `roomiepeace/tools/bill_tools.py` |
| B | 家事排班技能 | `roomiepeace/superpowers/chore_planner.py` | `roomiepeace/tools/chore_tools.py` |
| C | 衝突調解技能 | `roomiepeace/superpowers/conflict_mediator.py` | `roomiepeace/tools/text_tools.py`, `roomiepeace/guardrails.py` |
| D | 室友法庭技能 | `roomiepeace/superpowers/roomie_court.py` | `roomiepeace/tools/text_tools.py` |
| E | Karma 排行榜技能 | `roomiepeace/superpowers/karma_report.py` | `roomiepeace/tools/karma_tools.py` |

`line_announcement.py` 比較像整合 demo skill，建議由 integration owner 或最後報告負責人維護。

## 每個人主要改哪裡

每個 skill 的主流程都放在：

```text
roomiepeace/superpowers/{skill_name}.py
```

如果需要精準計算、資料處理、解析文字，請放在：

```text
roomiepeace/tools/{tool_name}.py
```

不要把計算邏輯塞在 Streamlit UI，也不要全部寫進自然語言模板。這個專案要展示的是 skill-based agent，所以要能清楚分出：

- Skill：任務流程怎麼走
- Tool：實際計算或資料處理
- Memory：記住事件
- Template / LLM fallback：產生自然語言回覆

## 請盡量不要同時改的檔案

這些是整合層，最容易發生 merge conflict：

```text
app.py
roomiepeace/agent.py
roomiepeace/router.py
data/memory.json
README.md
```

建議指定一位 integration owner 管這幾個檔案。其他人如果真的需要改，先在群組說一下。

## Skill 回傳格式

每個 skill 的 `handle(user_input, memory)` 最好維持同樣格式：

```python
return {
    "intent": "receipt_splitter",
    "skill": "receipt-splitter-skill",
    "response_markdown": markdown,
    "line_message": line_message,
    "tables": {"表格名稱": rows},
    "tools_used": ["tool_a", "tool_b"],
    "memory_updates": ["expense_created event"],
}
```

這樣 `app.py` 和 Agent Trace 就能直接顯示，不需要每個人另外接 UI。

## Memory 寫入規則

不要只把結果存在聊天文字裡。重要事件要寫進 event-based memory：

- 分帳：`expense_created`
- 家事排班：`chore_assigned`
- 衝突調解：`conflict_mediated`
- 室友法庭：`court_case_created`
- LINE 公告：`line_announcement_created`

寫入 memory 時請優先使用 `MemoryStore` 裡現有方法，例如：

```python
memory.record_expense(...)
memory.record_chore_assignments(...)
memory.record_conflict(...)
memory.record_court_case(...)
```

如果要新增 event type，請先確認其他 skill 會不會需要讀它。

## Guardrail 規則

搞笑可以，但不能變成霸凌。請避免：

- 外貌攻擊
- 性別、族群、疾病、家庭背景攻擊
- 人身羞辱
- 公開私人欠款或個資
- 假裝有法律效力
- 宣稱可以真的扣款或轉帳

如果輸出可能會貼到 LINE 群組，語氣要再保守一點。嘴砲版本可以好笑，但要像「任務吐槽」，不要像「人格攻擊」。

## Branch 命名建議

每個人從 `main` 開自己的 branch：

```bash
git checkout main
git pull
git checkout -b feature/receipt-splitter
```

建議命名：

```text
feature/receipt-splitter
feature/chore-planner
feature/conflict-mediator
feature/roomie-court
feature/karma-report
feature/ui-polish
feature/docs-demo-script
```

## Commit 建議

每次 commit 盡量小而清楚：

```bash
git add roomiepeace/superpowers/receipt_splitter.py roomiepeace/tools/bill_tools.py tests/test_bill_tools.py
git commit -m "Improve receipt splitter parsing"
```

不要用一個 commit 同時改五個 skill，會很難 review。

## Pull Request 檢查清單

開 PR 前請確認：

- `python -m pytest -q` 通過
- Streamlit app 可以啟動
- 自己負責的 quick prompt 可以跑
- Agent Trace 有顯示正確 skill 和 tools
- 沒有把 `.env`、快取檔、截圖暫存檔 commit 進來
- `data/memory.json` 沒有被 demo 過程改到奇怪狀態

## 測試方式

安裝依賴：

```bash
python -m pip install -r requirements.txt
```

跑測試：

```bash
python -m pytest -q
```

啟動 demo：

```bash
streamlit run app.py
```

## 新增一個 Skill 時要改哪些地方

如果未來要新增第六個 skill，通常需要改：

1. 新增 `roomiepeace/superpowers/new_skill.py`
2. 必要時新增 `roomiepeace/tools/new_tools.py`
3. 在 `roomiepeace/router.py` 加 intent keyword
4. 在 `roomiepeace/agent.py` 接上 handle
5. 在 `app.py` 加 quick prompt
6. 加測試到 `tests/`
7. 更新 README 或 demo script

如果只是改現有五個 skill，通常不用碰 `agent.py` 和 `app.py`。

## Demo 整合順序

最後整合時建議照這個順序測：

1. 建立室友資料
2. 分帳 demo
3. 家事排班 demo
4. 衝突調解 demo
5. 室友法庭 demo
6. LINE 群組公告
7. Karma 排行榜

這條故事線叫「冠宇與垃圾桶事件」。如果這條流程能順跑，報告基本就穩了。

## 一句話原則

每個人可以自由把自己的 skill 做得更有趣，但請守住三件事：

1. 計算交給 tool，不要交給文字生成。
2. 重要狀態寫進 memory，不要只顯示在畫面上。
3. 搞笑要有分寸，不要讓 RoomiePeace 變成室友戰爭啟動器。
