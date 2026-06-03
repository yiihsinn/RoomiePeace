# RoomiePeace Superpowers

Skill-based 共居生活協調 Agent：讓 AI Agent 幫室友處理分帳、家事、衝突提醒、室友法庭、LINE 公告和 Karma 排行榜。

RoomiePeace 不是普通聊天室。它會先用 deterministic Router 判斷 intent，再選擇對應 Superpower / Skill，呼叫 tools 做計算或排班，更新 event-based memory，通過 guardrail，最後產生可 demo 的結果與 Agent Trace。

## 為什麼有趣

室友問題通常不是「不知道答案」，而是「不知道怎麼講才不爆炸」。RoomiePeace 把共居生活拆成一組 Agent superpowers：

- 分帳要算得準，不能靠嘴。
- 家事要有 fairness，不然群組會安靜但心裡很吵。
- 衝突提醒要有效，但不能變成人身攻擊。
- 室友法庭要好笑，但必須清楚標示只是娛樂提醒。
- Karma 排行榜讓 demo 有記憶、有狀態、有戲劇張力。

## 系統架構

```text
User input
  -> Router
  -> selected Superpower / Skill
  -> Tool execution
  -> Memory update
  -> Guardrail check
  -> Final response + Agent Trace
```

主要檔案：

- `app.py`：Streamlit UI，包含三個 demo / 協作模式
- `roomiepeace/agent.py`：Agent orchestration
- `roomiepeace/router.py`：deterministic intent router
- `roomiepeace/memory.py`：JSON event-based memory
- `roomiepeace/guardrails.py`：安全檢查
- `roomiepeace/superpowers/`：各 superpower
- `roomiepeace/tools/`：deterministic tools
- `data/demo_scenarios.json`：Guided Demo 故事線
- `data/memory.json`：seed memory
- `TEAM_WORKFLOW.md`：八人協作必讀
- `docs/`：demo guideline、skill contract、evaluation 文件
- `tests/`：基本測試

## UI 模式

### Guided Demo

正式報告用。故事線是「冠宇與垃圾桶事件」，每一步都顯示：

- Step number / title / purpose
- Prompt
- Expected intent / expected skill
- Run this step button
- Output result
- LINE message
- Tables
- Agent Trace
- Memory updates

也提供：

- `Run full demo`
- `Reset demo memory`
- `Export demo transcript`

### Skill Sandbox

給 skill owner 單獨測自己的功能。可以選：

- `receipt_splitter`
- `chore_planner`
- `conflict_mediator`
- `roomie_court`
- `karma_report`
- `line_announcement`

Sandbox 預設仍走 `RoomiePeaceAgent.handle(prompt)`，不 bypass router。畫面會顯示 router 實際命中的 intent / skill，方便檢查 prompt 是否進到自己負責的 skill。

### Collaboration Dashboard

給小組協作用，集中顯示：

- 八人分工表
- 每個 role 的主要檔案與交付物
- Branch naming convention
- PR checklist
- 不要同時修改的檔案
- Skill output contract

## 八人分工

| Role | Owner | 主要範圍 |
| --- | --- | --- |
| A | Receipt Splitter Skill | 分帳解析、分類、金額計算 |
| B | Chore Planner Skill | 家事排班與公平性 |
| C | Conflict Mediator Skill | 衝突提醒、語氣風險、guardrail |
| D | Roomie Court Skill | 娛樂法庭判決 |
| E | Karma Report Skill | Karma 計分、稱號、排行榜 |
| F | UI / Dashboard | Streamlit 三模式 UI |
| G | Integration / Router / Memory / Trace | agent flow、router、event memory、trace |
| H | Demo / PPT / Video / Evaluation | demo 文案、錄影、評測設計 |

詳細規範請看 `TEAM_WORKFLOW.md`。

## Superpowers

### 1. receipt-splitter-skill

解析「阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65」這類輸入，判斷公用品和個人物品，呼叫 `split_bill` tool 精準計算分帳。金額不由 LLM 猜。

### 2. chore-planner-skill

根據室友限制、過去家事記錄和 difficulty 分數產生本週排班，並計算 fairness score。

### 3. conflict-mediator-skill

把抱怨轉成三種提醒版本：溫柔版、群組公告版、嘴砲但不失禮版。會避免人格攻擊和敏感內容。

### 4. roomie-court-skill

把室友糾紛包裝成娛樂用法庭判決，包含案件名稱、被告、證據、判決、理由和搞笑但合理的懲罰。明確聲明不具法律效力。

### 5. karma-report-skill

根據 memory 中的 expenses、chores、conflicts 和 court cases 計算 Karma 排行榜與稱號。

### 6. line-announcement-skill

加做的 demo skill：把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的文字。不串 LINE API。

## 安裝

```bash
cd roomiepeace-superpowers
python -m pip install -r requirements.txt
```

## 啟動

```bash
streamlit run app.py
```

開啟 Streamlit 顯示的網址，通常是：

```text
http://localhost:8501
```

## Demo 操作流程

1. 進入 `Guided Demo`
2. 按 `Reset demo memory`
3. 按 `Run full demo`，或依序點每個 step 的 `Run this step`
4. 展示每一步的 Agent Trace
5. 展示可貼到 LINE 群組的 `LINE message`
6. 最後展示 `Karma 排行榜`
7. 如需交給 H 做影片或 PPT，按 `Export demo transcript`

Guided Demo 的文案在 `data/demo_scenarios.json`，H 可以直接改 JSON，不需要改 `app.py`。

## Skill Owner 測試方式

1. 進入 `Skill Sandbox`
2. 在 `Select skill` 選自己的 skill
3. 先用 default prompt 跑
4. 再改 custom prompt 跑
5. 確認 router intent / selected skill 正確
6. 確認 output contract、tables、line_message、trace、memory updates
7. 必要時勾 `Reset memory before run`

Skill output contract：

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

## 測試

```bash
python -m pytest -q
```

目前測到：

- 分帳：公費 353 元、四人平分 88.25 元、非付款者各轉 88 元。
- Router：分帳、家事、衝突、法庭、Karma intent。
- Guardrail：正常搞笑 safe，人身攻擊 unsafe，法庭安全聲明 safe。
- Memory：分帳後新增 `expense_created`，家事排班後新增 `chore_assigned`。
- Demo scenario：`data/demo_scenarios.json` 能被讀取，每個 step 都有 prompt、expected intent、expected skill。

## Guardrail 規則

- 室友法庭只能作為娛樂與提醒，不假裝有法律效力。
- 嘴砲版本不能攻擊外貌、性別、家庭、疾病、族群等敏感項目。
- 分帳只提供建議，不做真實轉帳或扣款。
- 使用者要求公開私人欠款或個資時，會拒絕或建議匿名摘要。
- LINE 公告避免羞辱對方。

## Deterministic fallback

這個 prototype 不依賴外部 LLM，也不需要 API key。所有 demo 主流程都用規則、工具函式和模板產生，確保上課展示時不會因為網路或 key 出問題。

未來如果要加入 LLM，可以把它放在自然語言生成層，但金額計算、排班分數和 memory 更新仍應保留在 deterministic tools。

## 限制

- 收據解析目前支援簡單格式，例如 `品項129、品項159`。
- 家事排班是 prototype heuristic，不是最佳化演算法。
- Karma 分數是展示用，不代表真實道德評分。
- 不串 LINE API、不做轉帳、不處理真實法律問題。

## 未來可擴充

- 收據 OCR
- Google Sheet 同步
- LINE bot webhook
- 租屋契約 RAG
- 更完整的排班最佳化
- MCP-ready tool interface
- 匯出 demo 結果成 Markdown 檔案
