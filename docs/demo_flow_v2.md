# Demo Flow V2：冠宇與垃圾桶事件

這份文件給 H：Demo / PPT / Video / Evaluation owner 使用。正式 demo 建議直接使用 Streamlit 的 `Guided Demo` tab。

## Demo 前準備

1. 啟動 app：

```bash
streamlit run app.py
```

2. 進入 `Guided Demo`
3. 按 `Reset demo memory`
4. 確認右側或步驟內的 Agent Trace 區域會顯示 intent、skill、tools、memory updates

## 影片錄製順序

1. 開場展示三個 tabs：`Guided Demo`、`Skill Sandbox`、`Collaboration Dashboard`
2. 進入 `Guided Demo`
3. 按 `Reset demo memory`
4. 逐步點 7 個 steps 的 `Run this step`
5. 每一步都展示 Output result、LINE message、Tables、Agent Trace、Memory updates
6. 最後按 `Export demo transcript`
7. 切到 `Skill Sandbox`，展示 skill owner 可以選自己的 skill 測試
8. 切到 `Collaboration Dashboard`，展示八人分工表

## Step 1：建立室友資料

Prompt：

```text
我們有四個室友：阿明、小美、冠宇、庭萱。小美這週期中考，阿明週三晚上不在，冠宇常常忘記倒垃圾。
```

講稿：

> 第一個 step 是建立 RoomiePeace 的 event memory 基礎。這裡不是聊天紀錄，而是讓後面的分帳、排班和提醒都能讀到同一份室友狀態。

預期畫面：

- Expected intent：`setup_roommates`
- Expected skill：`roommate-setup`
- Output 顯示四位室友與 constraints
- Trace 顯示 `extract_roommates`、`extract_constraints`
- Memory updates 顯示 `roommate_setup_updated`

## Step 2：分帳 demo

Prompt：

```text
阿明買了衛生紙129、洗衣精159、餅乾89、垃圾袋65，幫我們分帳。
```

講稿：

> 第二步展示分帳技能。金額不是由 LLM 直接猜，而是由 deterministic tool `split_bill` 計算。衛生紙、洗衣精、垃圾袋是公用品，餅乾是阿明自己的快樂。

預期畫面：

- Expected intent：`receipt_splitter`
- Expected skill：`receipt-splitter-skill`
- 表格顯示品項分類
- 公費總額 353 元
- 四人平分每人 88.25 元
- 小美、冠宇、庭萱各轉阿明 88 元
- Memory updates 顯示 `expense_created`

## Step 3：家事排班 demo

Prompt：

```text
幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。
```

講稿：

> 第三步展示排班技能。系統會讀取前面建立的 constraints：小美期中考、阿明週三晚上不在、冠宇常常忘記倒垃圾，然後用 difficulty 分數安排任務。

預期畫面：

- Expected intent：`chore_planner`
- Expected skill：`chore-planner-skill`
- 倒垃圾分給冠宇
- 小美拿到較輕任務
- 顯示 fairness score
- Memory updates 顯示多筆 `chore_assigned`

## Step 4：衝突調解 demo

Prompt：

```text
冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。
```

講稿：

> 第四步展示衝突調解。系統不是幫忙罵人，而是把抱怨降級成三種可用提醒：溫柔版、群組公告版、嘴砲但不失禮版。

預期畫面：

- Expected intent：`conflict_mediator`
- Expected skill：`conflict-mediator-skill`
- 顯示語氣風險
- 顯示三種提醒版本
- Guardrail result 是 safe
- Memory updates 顯示 `conflict_mediated`

可唸出的句子：

```text
冠宇～垃圾桶目前已經進入最終型態，拜託你今晚拯救一下人類文明。
```

## Step 5：室友法庭 demo

Prompt：

```text
啟動室友法庭，幫我判決冠宇不倒垃圾。
```

講稿：

> 第五步是 demo 高潮：室友法庭。它會把糾紛包裝成娛樂判決，但明確聲明不具法律效力，避免真的法律風險。

預期畫面：

- Expected intent：`roomie_court`
- Expected skill：`roomie-court-skill`
- 顯示案件名稱、被告、證據、判決、判決理由
- LINE message 包含娛樂判決聲明
- Memory updates 顯示 `court_case_created`

## Step 6：LINE 群組公告

Prompt：

```text
幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。
```

講稿：

> 第六步展示這不是單點功能，而是會讀前面 memory，把分帳、家事和垃圾提醒整理成一段可以貼到 LINE 的公告。不串 LINE API，只產生文字。

預期畫面：

- Expected intent：`line_announcement`
- Expected skill：`line-announcement-skill`
- LINE message 有分帳、家事、系統提醒
- Tables 顯示家事與分帳項目
- Memory updates 顯示 `line_announcement_created`

## Step 7：Karma 排行榜

Prompt：

```text
產生本週 Karma 排行榜。
```

講稿：

> 最後用 Karma Report 收尾。它會讀取整個 demo 過程的 events，產生排行榜、稱號和本週共居狀態。

預期畫面：

- Expected intent：`karma_report`
- Expected skill：`karma-report-skill`
- 顯示 Karma 排行榜
- 顯示搞笑稱號
- 顯示 Garbage Disaster Index
- Memory updates 顯示 karma recalculated

## 收尾講法

> RoomiePeace 的重點不是純聊天，而是 skill-based agent。右邊 trace 可以看到每一步的 intent、skill、tools、memory updates 和 guardrail。這讓我們能展示 agent 真的有選技能、叫工具、更新記憶，而不是把所有事丟給黑箱文字生成。
