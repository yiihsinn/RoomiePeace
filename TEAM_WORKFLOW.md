# RoomiePeace 八人協作必讀

這份文件是給 8 個人同時開發與 demo 用的。目標是讓每個 skill owner 可以獨立測自己的功能，UI / integration / demo owner 可以穩定整合，最後上台時不用靠口頭記憶硬撐。

## 分工總覽

| 成員 | Role | 主要檔案 | 交付物 |
| --- | --- | --- | --- |
| A | Receipt Splitter Skill | `roomiepeace/superpowers/receipt_splitter.py`, `roomiepeace/tools/bill_tools.py`, `tests/test_bill_tools.py` | 分帳解析、品項分類、金額計算與測試 |
| B | Chore Planner Skill | `roomiepeace/superpowers/chore_planner.py`, `roomiepeace/tools/chore_tools.py` | 家事排班、difficulty 分數、公平性說明 |
| C | Conflict Mediator Skill | `roomiepeace/superpowers/conflict_mediator.py`, `roomiepeace/tools/text_tools.py`, `roomiepeace/guardrails.py` | 三種提醒版本、語氣風險、guardrail |
| D | Roomie Court Skill | `roomiepeace/superpowers/roomie_court.py`, `roomiepeace/tools/text_tools.py` | 法庭格式、證據、判決理由、娛樂免責 |
| E | Karma Report Skill | `roomiepeace/superpowers/karma_report.py`, `roomiepeace/tools/karma_tools.py` | Karma 計分、排行榜、稱號、共居狀態 |
| F | UI / Dashboard | `app.py`, `docs/demo_script.md` if needed | Guided Demo、Skill Sandbox、Dashboard 體驗 |
| G | Integration / Router / Memory / Trace | `roomiepeace/agent.py`, `roomiepeace/nlu.py`, `roomiepeace/router.py`, `roomiepeace/memory.py`, `roomiepeace/trace.py`, `data/memory.json` | Gemini NLU、agent flow、router、event memory、trace、整合測試 |
| H | Demo / PPT / Video / Evaluation | `data/demo_scenarios.json`, `data/demo_nlu_cache.json`, `docs/demo_flow_v2.md`, `docs/project_overview.md`, `README.md`, `docs/evaluation_plan.md` | demo 講稿、Gemini demo cache、錄影順序、PPT 素材、評測方式 |

`line_announcement.py` 是 demo 整合 skill，建議由 G 或 H 維護，因為它會讀取前面步驟產生的 memory。

## 核心架構不要打掉

請維持這條 flow：

```text
User input
  -> cached Gemini demo extraction if prompt is in data/demo_nlu_cache.json
  -> Vertex Gemini NLU extraction if configured and cache misses
  -> deterministic fallback if needed
  -> Router
  -> selected Superpower / Skill
  -> Tool execution
  -> Memory update
  -> Guardrail check
  -> Final response + Agent Trace
```

如果只是改現有 skill，通常不需要碰 `app.py`、`agent.py` 或 `router.py`。

正式 demo 的 7 個 prompts 會優先使用 `data/demo_nlu_cache.json`，所以沒有 API key 的隊友也能看到 `Cached Gemini` NLU 結果，demo 不需要等即時 API。H 如果修改 `data/demo_scenarios.json` 裡的 prompt，要同步更新 `data/demo_nlu_cache.json`。

## 每個人主要改哪裡

每個 skill 的主流程放在：

```text
roomiepeace/superpowers/{skill_name}.py
```

精準計算、排班、文字解析、Karma 分數等 deterministic logic 放在：

```text
roomiepeace/tools/{tool_name}.py
```

不要把計算邏輯塞進 UI，也不要讓 LLM 或模板直接算錢、算公平分數、改 memory。

## 請避免同時改的檔案

這些是整合層或共用文件，最容易 merge conflict：

```text
app.py
roomiepeace/agent.py
roomiepeace/router.py
roomiepeace/memory.py
data/memory.json
README.md
```

需要改這些檔案時，先在群組說一聲。F 管 UI，G 管 integration，H 管 demo 文案，彼此要先對齊。

## Skill 回傳格式

每個 skill 的 `handle(user_input, memory)` 要維持同樣 contract：

```python
return {
    "intent": "...",
    "skill": "...",
    "response_markdown": "...",
    "line_message": "...",
    "tables": {...},
    "tools_used": [...],
    "memory_updates": [...]
}
```

UI、Skill Sandbox、Guided Demo 和 Agent Trace 都靠這個格式顯示結果。

## Memory 寫入規則

不要只把結果存在聊天文字裡。重要事件要寫進 event-based memory：

- 分帳：`expense_created`
- 家事排班：`chore_assigned`
- 衝突調解：`conflict_mediated`
- 室友法庭：`court_case_created`
- LINE 公告：`line_announcement_created`

請優先使用 `MemoryStore` 既有方法：

```python
memory.record_expense(...)
memory.record_chore_assignments(...)
memory.record_conflict(...)
memory.record_court_case(...)
```

如果要新增 event type，先確認 Karma、LINE 公告、Dashboard 會不會需要讀它。

## Guardrail 規則

搞笑可以，但不能變成霸凌。請避免：

- 外貌攻擊
- 性別、族群、疾病、家庭背景攻擊
- 人身羞辱
- 公開私人欠款或個資
- 假裝有法律效力
- 宣稱可以真的扣款或轉帳

LINE 群組公告要比私訊更保守。嘴砲版本可以好笑，但要像「任務吐槽」，不要像「人格攻擊」。

## Skill Sandbox 使用方式

Skill owner merge 前都要做：

1. 啟動 app：`streamlit run app.py`
2. 進入 `Skill Sandbox`
3. 在 `Select skill` 選自己的 skill
4. 先跑 default prompt
5. 再輸入 custom prompt
6. 確認 router 命中自己的 intent / skill
7. 確認 output contract、tables、line_message、trace、memory updates 都正常
8. 有需要時勾 `Reset memory before run`

如果 router 沒命中自己的 skill，請找 G 一起調整 `roomiepeace/router.py`。

## Guided Demo 使用方式

正式 demo 請走 `Guided Demo` tab：

1. 按 `Reset demo memory`
2. 按 `Run full demo`，或逐步點每個 step 的 `Run this step`
3. 展示每一步的 Output result、LINE message、Tables、Agent Trace、Memory updates
4. 按 `Export demo transcript` 產生 markdown，給 H 做影片或 PPT 素材

Demo 流程資料在：

```text
data/demo_scenarios.json
```

H 可以改 demo 文案，不需要改 `app.py`。

## Branch 命名建議

每個人從 `main` 開自己的 branch：

```bash
git checkout main
git pull
git checkout -b feature/receipt-splitter
```

建議 branch：

```text
feature/receipt-splitter
feature/chore-planner
feature/conflict-mediator
feature/roomie-court
feature/karma-report
feature/ui-guided-demo
feature/integration-router-memory
feature/docs-demo-video
```

## Commit 建議

每次 commit 盡量小而清楚：

```bash
git add roomiepeace/superpowers/receipt_splitter.py roomiepeace/tools/bill_tools.py tests/test_bill_tools.py
git commit -m "Improve receipt splitter parsing"
```

不要一個 commit 同時改五個 skill，review 會很痛。

## Pull Request 檢查清單

開 PR 前請確認：

- `python -m pytest -q` 通過
- Streamlit app 可以啟動
- Skill Sandbox default prompt 跑過
- Skill Sandbox custom prompt 跑過
- Agent Trace 顯示正確 intent、skill、tools 和 memory updates
- 沒有把 `.env`、cache、截圖暫存檔 commit 進來
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

1. 新增 `roomiepeace/superpowers/new_skill.py`
2. 必要時新增 `roomiepeace/tools/new_tools.py`
3. 在 `roomiepeace/router.py` 加 intent keyword
4. 在 `roomiepeace/agent.py` 接上 handle
5. 在 `app.py` 的 Skill Sandbox 加設定
6. 必要時在 `data/demo_scenarios.json` 加 demo step
7. 加測試到 `tests/`
8. 更新 `docs/skill_contract.md` 或 README

## Demo 整合順序

最後整合時照這條故事線測：

1. 建立室友資料
2. 分帳 demo
3. 家事排班 demo
4. 衝突調解 demo
5. 室友法庭 demo
6. LINE 群組公告
7. Karma 排行榜

故事線叫「冠宇與垃圾桶事件」。如果 Guided Demo 能完整跑完，報告基本就穩。

## 一句話原則

每個人可以自由把自己的 skill 做得更有趣，但請守住三件事：

1. 計算交給 tool，不要交給文字生成。
2. 重要狀態寫進 memory，不要只顯示在畫面上。
3. Merge 前一定到 Skill Sandbox 測自己的 skill。
