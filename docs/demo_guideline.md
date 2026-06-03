# Demo Guideline：冠宇與垃圾桶事件

這份是正式上台用的 demo guideline。重點不是把每個功能念完，而是讓觀眾清楚看到：

1. 這不是普通 chatbot。
2. Agent 會 route 到不同 skill。
3. Skill 會呼叫 deterministic tools。
4. 每一步會更新 event-based memory。
5. 室友法庭會讀前面 memory，展示「累犯加重處罰」。
6. 整體輸出好笑，但沒有霸凌，也不假裝有法律效力。

## Demo 前設定

開啟：

```bash
streamlit run app.py
```

瀏覽器進入：

```text
http://localhost:8501
```

進入 `Guided Demo` tab，先按：

```text
Reset demo memory
```

建議不要一開始按 `Run full demo`。正式展示比較適合逐步按 `Run current step`，因為每一步可以講清楚 Agent Pipeline、NLU summary、Agent Trace 和 memory updates。

## 開場台詞

> 我們的題目是 RoomiePeace Superpowers。它不是一般室友聊天 app，而是 skill-based agent。
> 我們有接 Vertex Gemini 做 NLU extraction：Gemini 先把自然語言抽成 payer、items、target、topic 這些 structured fields。
> 接著 skill 會呼叫 deterministic tools 做計算、排班、累犯判斷和 memory 更新。
> 等一下大家可以看 Guided Demo 裡的 Agent Pipeline 和 NLU summary：每一步都會顯示 Gemini 或 fallback 如何抽欄位、router 判斷出的 intent、選到哪個 skill、呼叫哪些 tools、更新哪些 memory。
> 今天故事線叫「冠宇與垃圾桶事件」，主角不是壞人，只是跟倒垃圾任務有一段不太健康的遠距離關係。

畫面操作：

- 指一下三個 tabs：`Guided Demo`、`Skill Sandbox`、`Collaboration Dashboard`
- 回到 `Guided Demo`
- 指上方 metrics：Progress、Memory events、Garbage index、Latest skill

## Step 1：建立室友資料

按左側 Step 1，按 `Run current step`。

Prompt：

```text
我們有四個室友：阿明、小美、冠宇、庭萱。小美這週期中考，阿明週三晚上不在，冠宇常常忘記倒垃圾。
```

台詞：

> 第一步先建立共居 memory。這裡不是存聊天紀錄，而是建立室友名單和本週 constraints。
> 注意冠宇這裡被標記為「常常忘記倒垃圾」，這不是現在就處罰他，而是後面法庭會讀到的背景紀錄。

要指給觀眾看的地方：

- Expected intent：`setup_roommates`
- Actual intent：`setup_roommates`
- Trace 裡的 `nlu_result.source`
- Memory updates：`roommate_setup_updated`
- Sidebar 的室友狀態

小笑點：

> 這一步等於系統先建案，但目前還沒有開庭，冠宇還有機會回頭。

## Step 2：分帳 demo

按 Step 2，按 `Run current step`。

Prompt：

```text
今天阿明先幫大家墊了公共用品，衛生紙129元、洗衣精159元、垃圾袋65元，另外餅乾89元是他自己買來快樂的，幫我們分帳並算誰要轉多少。
```

台詞：

> 第二步展示分帳。這句話刻意比較像真實群組訊息，不是固定收據格式。
> 金額不能交給語言模型自由發揮，所以 RoomiePeace 會呼叫 deterministic tool。
> Gemini 只負責把自然語言抽成 payer、items 和 personal item，真正的公費總額與轉帳建議由 `split_bill` 算。
> 衛生紙、洗衣精、垃圾袋是公用品；餅乾是阿明自己的快樂，不列入公費。

要指給觀眾看的地方：

- Table：品項判斷
- Table：轉帳建議
- 公費總額：353 元
- 每人：88.25 元
- 小美、冠宇、庭萱各轉阿明 88 元
- Agent Pipeline：`NLU -> Router -> Skill -> Tools -> Memory`
- NLU summary：payer 是阿明，三個 shared items，一個 personal item
- Trace 裡的 `parse_receipt_items`、`split_bill`
- 如果有 Vertex credentials，Trace 會顯示 `nlu_result.source = vertex_gemini_structured_output`
- Memory updates：`expense_created`

小笑點：

> 我們不會真的轉帳，RoomiePeace 目前沒有魔法金融權限，只有很會算跟很會講。

可補充：

> 如果使用者用比較自然的句子，例如「阿明先墊了衛生紙129元、洗衣精159元」，Gemini NLU 會先抽欄位；如果沒有 API 或抽不到欄位，系統會 fallback 或要求澄清，不會亂寫 memory。

## Step 3：家事排班 demo

按 Step 3，按 `Run current step`。

Prompt：

```text
幫我們排這週家事。任務有倒垃圾、拖地、洗浴室、補衛生紙。
```

台詞：

> 第三步是家事排班。系統會讀剛剛的 constraints：小美期中考，所以安排輕任務；阿明週三不在，所以避開；冠宇常常忘記倒垃圾，所以被排回倒垃圾。
> 這裡不是報復，是排班正義。

要指給觀眾看的地方：

- Table：家事排班
- 冠宇：倒垃圾
- 小美：補衛生紙
- Fairness score
- Trace 裡的 `generate_chore_schedule`
- Memory updates：`chore_assigned`

累犯伏筆：

> 到目前為止，冠宇已經有一筆背景紀錄，加上一筆正式排班紀錄。法庭還沒開，但檔案夾已經變厚。

## Step 4：衝突調解 demo

按 Step 4，按 `Run current step`。

Prompt：

```text
冠宇又忘記倒垃圾，但我不想跟他吵架，幫我提醒他。
```

台詞：

> 第四步展示衝突調解。室友最難的不是知道要倒垃圾，而是怎麼提醒對方又不撕破臉。
> 所以系統會產生三種版本：溫柔版、群組公告版、嘴砲但不失禮版。

要指給觀眾看的地方：

- 語氣風險分析
- 三種提醒版本
- Guardrail safe
- Memory updates：`conflict_mediated`

可以念的句子：

```text
冠宇～垃圾桶目前已經進入最終型態，拜託你今晚拯救一下人類文明。
```

累犯伏筆：

> 現在多了一筆提醒紀錄。也就是說，等一下法庭不是突然發瘋，是根據 memory 說：你已經被提醒過了。

## Step 5：室友法庭 demo

按 Step 5，按 `Run current step`。

Prompt：

```text
啟動室友法庭，幫我判決冠宇不倒垃圾。
```

台詞：

> 第五步是 demo 高潮：室友法庭。
> 請注意這裡的「累犯加重」不是亂加的。系統讀到三個 prior records：
> 第一，冠宇的背景狀態是常常忘記倒垃圾。
> 第二，他剛剛被正式排入倒垃圾任務。
> 第三，衝突調解已經提醒過一次。
> 所以這裡累犯指數是 3，進入累犯加重。重點是：加重的是任務，不是攻擊人格。

要指給觀眾看的地方：

- 累犯紀錄
- 累犯依據區塊：memory 讀到的前情提要
- 累犯指數：`3（累犯加重）`
- 判決摘要 table
- LINE message 裡的「本案只審任務，不審人格」
- Trace 裡的 `count_prior_incidents`
- Memory updates：`court_case_created`

可以念的句子：

```text
本庭認為，垃圾桶不是許願池，放著不會自動清空；本案已有 3 筆前情提要，因此加重的是任務提醒，不是人格審判。
```

笑點節奏：

> 這不是法律判決，這是室友和平的情境劇。法律上不具效力，但群組裡可能很有威嚴。

## Step 6：LINE 群組公告

按 Step 6，按 `Run current step`。

Prompt：

```text
幫我把本週分帳、家事和垃圾提醒整理成可以貼到 LINE 群組的公告。
```

台詞：

> 第六步展示 memory 的整合能力。它不是重新問一次，而是讀前面已經發生的 expense、chore、court case，整理成 LINE 群組公告。
> 所以公告裡會有分帳、家事、垃圾提醒，還有剛剛法庭的累犯加重處分。

要指給觀眾看的地方：

- LINE message
- 分帳 section
- 家事 section
- 室友法庭 section
- Tables 裡的室友法庭摘要

小笑點：

> 這段可以直接貼群組，但建議貼之前先深呼吸，畢竟我們追求的是和平，不是開戰。

## Step 7：Karma 排行榜

按 Step 7，按 `Run current step`。

Prompt：

```text
產生本週 Karma 排行榜。
```

台詞：

> 最後用 Karma 排行榜收尾。它會讀整個 demo 過程的 events，像分帳、排班、提醒、法庭，產生排行榜和稱號。
> 這讓我們看到 Agent 不只是一次性回答，而是會根據生活事件累積狀態。

要指給觀眾看的地方：

- Karma 排行榜
- 搞笑稱號
- Garbage Disaster Index
- Trace 裡的 `compute_karma`

收尾句：

> RoomiePeace 的核心不是聊天，而是 skill-based agent。Gemini 負責理解自然語言，skills 和 tools 負責流程與正確性，memory 負責狀態，guardrail 負責控制笑話的邊界。
> 我們讓它好笑，但不讓它變成室友戰爭啟動器。

## 如果時間很短

3 分鐘版：

1. Step 1 建立資料
2. Step 2 分帳，展示 tool 精算
3. Step 4 衝突調解，展示 guardrail
4. Step 5 室友法庭，展示累犯加重
5. Step 6 LINE 公告，展示 memory 整合

可以略過 Step 3 的細節，但不要真的不跑 Step 3，因為累犯指數需要排班紀錄。

## Demo 注意事項

- 每一步都先看 Expected intent，再看 Actual intent。
- 一定要展示 Agent Trace，這是跟普通 chatbot 的差異。
- 室友法庭要強調「只審任務，不審人格」。
- 不要說這是真的法律判決。
- 不要說系統會真的轉帳或真的發 LINE。
- 笑點放在任務荒謬，不放在人身攻擊。
