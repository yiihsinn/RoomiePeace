# Demo Script：冠宇與垃圾桶事件

這份腳本可以直接拿來上台 demo。建議先按左側 `重置 demo memory`，再照順序跑 quick prompts。

## 0. 開場

一句話介紹：

> RoomiePeace 不是普通室友聊天室，而是 Skill-based 共居生活協調 Agent。它會先用 Vertex Gemini 或 deterministic fallback 抽出 structured task fields，再判斷 intent、啟動 skill、呼叫 deterministic tools、更新 event-based memory，最後產生 LINE 公告和 trace。

請觀眾注意 Agent Pipeline、NLU summary 和 Agent Trace：

- `intent`
- `nlu_result.source`
- `selected_superpower`
- `tools_used`
- `memory_updates`
- `guardrail_result`

## 1. 建立室友資料

輸入：

```text
我們有四個室友：阿明、小美、冠宇、庭萱。小美這週期中考，阿明週三晚上不在，冠宇常常忘記倒垃圾。
```

講解：

- Agent 進入 `roommate-setup`
- Memory 更新室友與本週 constraints
- Sidebar 會顯示每個人的狀態

## 2. 分帳

輸入：

```text
今天阿明先幫大家墊了公共用品，衛生紙129元、洗衣精159元、垃圾袋65元，另外餅乾89元是他自己買來快樂的，幫我們分帳並算誰要轉多少。
```

預期重點：

- 進入 `receipt-splitter-skill`
- 有 Vertex credentials 時，`nlu_result.source` 會顯示 `vertex_gemini_structured_output`
- NLU summary 會顯示 payer 是阿明，抽到三個公用品和一個個人物品
- `parse_receipt_items` 解析品項
- `split_bill` 算出公費 353 元
- 四人平分每人 88.25 元
- 小美、冠宇、庭萱各轉阿明 88 元
- 餅乾被判定為阿明個人物品
- Memory 新增 `expense_created`

## 3. 家事排班

輸入：

```text
幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。
```

預期重點：

- 進入 `chore-planner-skill`
- 倒垃圾分給冠宇，因為 memory 裡有常常忘記倒垃圾
- 小美考試週被安排輕任務
- 產生 fairness score
- Memory 新增多筆 `chore_assigned`

## 4. 衝突調解

輸入：

```text
冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。
```

預期重點：

- 進入 `conflict-mediator-skill`
- 產生溫柔版、群組公告版、嘴砲但不失禮版
- Guardrail 保持 safe
- Memory 新增 `conflict_mediated`

可以唸出嘴砲版：

```text
冠宇～垃圾桶目前已經進入最終型態，拜託你今晚拯救一下人類文明。
```

## 5. 室友法庭

輸入：

```text
啟動室友法庭，幫我判決冠宇不倒垃圾。
```

預期重點：

- 進入 `roomie-court-skill`
- 產生案件名稱、證據、判決與理由
- 顯示累犯依據：背景狀態、家事排班、衝突提醒三筆 memory
- 累犯指數為 3，啟動加重但不霸凌的處分
- 明確聲明只是娛樂提醒，不具法律效力
- Memory 新增 `court_case_created`

## 6. LINE 群組公告

輸入：

```text
幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。
```

預期重點：

- 進入 `line-announcement-skill`
- 從 memory 讀取最新分帳與家事
- 產生可以直接貼到 LINE 的公告

## 7. Karma 排行榜

輸入：

```text
產生本週 Karma 排行榜。
```

預期重點：

- 進入 `karma-report-skill`
- 根據 memory events 重新計算 Karma
- 顯示稱號與本週共居狀態

## 收尾

可以強調：

- Agent 不是黑箱聊天，因為 trace 顯示它選了哪個 skill、用了哪些 tools、更新哪些 memory。
- 有 Vertex credentials 時可展示 Gemini structured extraction；沒有 credentials 時 fallback 也能跑，demo 穩定。
- 真實金流、LINE API、法律判決都沒有真的執行，符合 prototype 和 guardrail 範圍。
