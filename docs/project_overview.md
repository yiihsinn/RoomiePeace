# Project Overview

RoomiePeace Superpowers 是一個課程小組專題 prototype，目標是展示「Skill-based AI Agent」如何處理共居生活問題。

## 核心概念

一般 chatbot 常常直接生成文字，但 RoomiePeace 把任務拆成：

1. Demo prompt 先讀 Cached Gemini structured extraction；自由輸入可用 Vertex Gemini NLU，沒有 credentials 時走 deterministic fallback
2. Router 判斷任務類型
3. Skill 決定流程
4. Tool 做精確計算或資料處理
5. Memory 記錄生活事件
6. Guardrail 避免不適當輸出
7. UI 顯示結果與 trace

Gemini 負責理解欄位，tools 負責正確性。分帳金額、排班分數、累犯指數和 memory 更新都不交給 LLM。

## Event-Based Memory

`data/memory.json` 不只存聊天紀錄，而是存生活事件。

事件例子：

```json
{
  "event_type": "expense_created",
  "timestamp": "2026-06-01T20:30:00",
  "actor": "阿明",
  "data": {
    "items": ["衛生紙", "洗衣精", "垃圾袋"],
    "shared_total": 353,
    "split_members": ["阿明", "小美", "冠宇", "庭萱"]
  }
}
```

這讓後續 skill 可以讀取過去發生什麼，例如：

- LINE 公告讀取最新分帳與排班
- Karma 根據 expense、chore、conflict、court events 計分
- Sidebar dashboard 顯示最新狀態

## Deterministic Tools

這個 prototype 的關鍵計算不交給 LLM：

- `bill_tools.split_bill`：分帳金額
- `chore_tools.generate_chore_schedule`：家事排班
- `chore_tools.calculate_fairness_score`：公平分數
- `karma_tools.compute_karma`：Karma 分數
- `guardrails.guardrail_check`：安全檢查

## Optional Vertex Gemini NLU

`roomiepeace/nlu.py` 會在 `.env` 有 Vertex 設定時呼叫 Gemini structured output，把自然語言抽成：

```json
{
  "intent": "receipt_splitter",
  "payer": "阿明",
  "items": [
    {"name": "衛生紙", "amount": 129, "classification": "shared"}
  ],
  "target": "",
  "topic": "分帳",
  "missing_fields": []
}
```

Guided Demo 的固定 prompts 會先讀 `data/demo_nlu_cache.json`，Trace 顯示 `cached_vertex_gemini_structured_output`。這讓沒有 API 的隊友也能看到同一份 Gemini structured extraction，正式 demo 也不用等 API。

如果 cache 沒命中但 Vertex 可用，系統會即時呼叫 Gemini；如果 Vertex 不可用，系統會退回 deterministic parser。Trace 會顯示 `nlu_result.source`，讓 demo 時可以清楚看到是 `cached_vertex_gemini_structured_output`、`vertex_gemini_structured_output` 還是 `deterministic_fallback`。

## UI Layout

Streamlit app 現在分成三個 tabs：

- Guided Demo：正式報告用，依序跑「冠宇與垃圾桶事件」7 steps，並顯示 Agent Pipeline、NLU summary、output、LINE message、tables、Agent Trace 和 memory updates。
- Skill Sandbox：給 skill owners 單獨測試自己的 default prompt 與 custom prompt，仍然透過 `RoomiePeaceAgent.handle()`，不 bypass router，也顯示 pipeline 和 NLU extraction 結果。
- Collaboration Dashboard：顯示八人分工、branch naming、PR checklist、不要互踩的檔案和 skill output contract。

Sidebar 仍然保留 dashboard：

- 室友名單與狀態
- 公用品庫存
- 未結清款項
- Garbage Disaster Index
- Karma 排行榜
- 家事完成紀錄

## Prototype Scope

有做：

- 五個必做 superpowers
- 加做 LINE announcement skill
- JSON memory persistence
- External demo scenario JSON
- Guided Demo / Skill Sandbox / Collaboration Dashboard
- Guardrail
- Tests
- README、team workflow、demo flow、skill contract 和 evaluation docs

沒做：

- 真正 LINE API
- 真實轉帳
- 真正法律判決
- OCR
- Live LLM 生成最終文字

## Demo 評分亮點

- 可以從 trace 證明它不是單純 chatbot。
- 分帳和排班由 deterministic tools 完成。
- 每一步都更新 event memory。
- 輸出有趣，但 guardrail 維持界線。
- 有 Vertex credentials 時可展示 Gemini NLU；沒有 credentials 時 fallback 仍可跑。
