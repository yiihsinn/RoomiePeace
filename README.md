# RoomiePeace Superpowers

Skill-based 共居生活協調 Agent：讓 AI Agent 幫室友處理分帳、家事、衝突提醒、室友法庭和 Karma 排行榜。

這不是普通聊天室。RoomiePeace 會先用 Router 判斷使用者 intent，再選擇對應 Superpower / Skill，呼叫 deterministic tools 做計算或排班，更新 event-based memory，最後產生可貼到 LINE 群組的結果與 Agent Trace。

## 為什麼有趣

室友問題通常不是「不知道答案」，而是「不知道怎麼講才不爆炸」。這個 prototype 把共居生活拆成幾個 Agent superpowers：

- 分帳要算得準，不能靠嘴。
- 家事要有 fairness，不然群組會安靜但心裡很吵。
- 衝突提醒要有效，但不能變成人身攻擊。
- 室友法庭要好笑，但必須清楚標示只是娛樂提醒。
- Karma 排行榜讓 demo 有記憶、有狀態、有戲劇張力。

## 系統架構

```text
RoomiePeace Agent
  ├── Router：用關鍵字判斷 intent
  ├── Superpowers / Skills：定義任務流程
  ├── Tools：做金額計算、排班、Karma 和文字解析
  ├── Memory：JSON event-based memory
  ├── Guardrail：避免霸凌、隱私外洩、真實金流或假法律效力
  └── UI：Streamlit dashboard + input + trace
```

主要檔案：

- `app.py`：Streamlit demo UI
- `roomiepeace/agent.py`：Agent orchestration
- `roomiepeace/router.py`：intent router
- `roomiepeace/memory.py`：JSON memory store
- `roomiepeace/guardrails.py`：安全檢查
- `roomiepeace/superpowers/`：各 superpower
- `roomiepeace/tools/`：deterministic tools
- `data/memory.json`：seed memory
- `tests/`：基本測試
- `TEAM_WORKFLOW.md`：五人分工必讀與開發規範

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

## Demo 流程：「冠宇與垃圾桶事件」

在頁面上方依序點 quick prompts：

1. `建立室友資料`
2. `分帳 demo`
3. `家事排班 demo`
4. `衝突調解 demo`
5. `室友法庭 demo`
6. `LINE 群組公告`
7. `Karma 排行榜`

Demo 重點可以這樣講：

- 左側 Dashboard 會顯示室友狀態、公用品庫存、未結清款項、Garbage Disaster Index、Karma 和家事記錄。
- 中間是 Agent 回覆和可貼到 LINE 的訊息。
- 右側 Agent Trace 會顯示 user input、intent、selected superpower、tools used、memory updates 和 guardrail result。

## 測試

```bash
python -m pytest -q
```

目前測到：

- 分帳：公費 353 元、四人平分 88.25 元、非付款者各轉 88 元。
- Router：分帳、家事、衝突、法庭、Karma intent。
- Guardrail：正常搞笑 safe，人身攻擊 unsafe，法庭安全聲明 safe。
- Memory：分帳後新增 `expense_created`，家事排班後新增 `chore_assigned`。

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
- 匯出 demo 結果成 Markdown
