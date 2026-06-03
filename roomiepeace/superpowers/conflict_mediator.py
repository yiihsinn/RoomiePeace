"""RoomiePeace: Conflict Mediator Skill."""

from __future__ import annotations

from typing import Any

from ..guardrails import soften_for_group, guardrail_check
from ..memory import MemoryStore
from ..tools.text_tools import extract_target, extract_topic


def _analyze_risk(text: str) -> tuple[int, str]:
    """動態計算風險分數並生成客製化的分析文案"""
    score = 45
    triggers = []
    
    if "又" in text:
        score += 18
        triggers.append("「又」")
    if "每次" in text:
        score += 15
        triggers.append("「每次」")
    if "不想吵架" in text:
        score += 8
    if "你" in text and "都" in text:
        score += 10
        triggers.append("「你...都...」")
        
    final_score = min(90, score)
    
    if triggers:
        trigger_str = " 及 ".join(triggers)
        analysis_text = f"偵測到文句中包含 {trigger_str} 等強烈指責詞，容易讓對方產生被貼標籤的強烈防衛心理（預估防衛反應 **{final_score}%**）。建議去除情緒化字眼，轉化為客觀事實描述。"
    else:
        analysis_text = f"目前語氣相對克制（預估防衛反應 **{final_score}%**）。建議維持中性且具體的需求說明，以獲得最高配合度。"
        
    return final_score, analysis_text


def handle(user_input: str, memory: MemoryStore) -> dict[str, Any]:
    # 1. 執行 Guardrail 安全檢查
    safety = guardrail_check(user_input)
    if not safety["safe"]:
        issues_str = ", ".join(safety["issues"])
        return {
            "intent": "conflict_mediator",
            "skill": "conflict-mediator-skill",
            "response_markdown": f"### ⚠️ 衝突調解失敗\n\n> **系統阻斷原因**：偵測到違規用語 ({issues_str})\n\n**防護建議**：{safety['suggestion']}\n\n請重新輸入溫和一點的抱怨吧！",
            "line_message": "【系統阻斷】輸入包含違規語氣，無法產生群組公告。",
            "tables": {},
            "tools_used": ["guardrail_check"],
            "memory_updates": []
        }

    # 2. 解析內容與計算風險
    snapshot = memory.snapshot()
    target = extract_target(user_input, snapshot["roommates"])
    topic = extract_topic(user_input)
    
    # 修正：如果工具沒抓到明確主題，給予一個體面的預設值
    if not topic or topic == "共居任務":
        topic = "生活作息與習慣規範"
        
    risk_score, risk_analysis = _analyze_risk(user_input)
    
    # 3. 寫入 Event Memory
    event = memory.record_conflict(target, topic, risk_score)

    # 4. 產生多種語氣版本 (升級為兼顧家事與行為問題的萬用模板)
    # 4. 產生多種語氣版本 (超全面複合模板，完美兼顧各種日常共居衝突)
    
    # 情境一：倒垃圾
    if topic == "倒垃圾" or "垃圾" in user_input:
        topic = "倒垃圾"
        gentle = f"{target}～提醒一下今天垃圾好像輪到你，現在有點滿了，你方便等等拿下去嗎？感謝！"
        group = f"【家事提醒】本日垃圾任務輪到 {target}。垃圾桶目前已接近滿載，請抽空協助處理，感謝配合。"
        playful = f"{target}～垃圾桶目前已經進入最終型態，快要撐破結界了！拜託你今晚揮灑熱血拯救一下人類文明。"
        
    # 情境二：洗碗
    elif topic == "洗碗" or "碗盤" in user_input or "水槽" in user_input:
        topic = "洗碗與水槽整潔"
        gentle = f"{target}～水槽裡的碗盤好像是你的，有空可以幫忙洗一下嗎？免得引來小蟲子，謝謝你喔！"
        group = f"【公共區域公告】目前水槽已接近無空間狀態，請負責洗碗的 {target} 盡速協助清理，維持廚房衛生。"
        playful = f"{target}～{target}！水槽裡的碗盤已經堆疊出新的幾何高度，再不洗就要誕生新的生態系了，救救大家！"
        
    # 情境三：噪音/深夜放音樂/大聲講話
    elif "音樂" in user_input or "吵" in user_input or "聲音" in user_input or "大聲" in user_input:
        topic = "深夜音量控制"
        gentle = f"{target}～不好意思，因為現在時間比較晚了，聲音在房間聽得滿清楚的，方便幫我戴個耳機或關小聲一點嗎？謝謝你！"
        group = f"【共居生活公約】溫馨提醒各位室友，深夜（23:00後）請放低音量、自備耳機，共同維護彼此的睡眠品質，感謝大家！"
        playful = f"{target}～偵測到強大的低音重低音正在震撼公館！大家快被熱情的音波超渡了，求求大師收了神通，切換成靜音模式吧！"
        
    # 情境四：洗浴室/毛髮堵塞排水孔
    elif "浴室" in user_input or "洗澡" in user_input or "頭髮" in user_input or "排水孔" in user_input:
        topic = "浴室清潔與排水孔毛髮"
        gentle = f"{target}～提醒一下排水孔好像有點被頭髮卡住了，水流得有點慢，洗完澡有空的話再麻煩順手清一下，謝啦！"
        group = f"【公共區域維護】請各位室友於使用完浴室後，順手清理排水孔之毛髮及個人遺留用品，維持良好的排水環境，感謝配合。"
        playful = f"{target}～浴室的排水孔正在遭遇嚴重的「堵塞封印」，水積到快可以泛舟了！懇請 {target} 施展順手清理魔功，拯救大家！"
        
    # 情境五：冰箱/偷吃或偷喝別人的東西
    elif "冰箱" in user_input or "偷吃" in user_input or "飲料" in user_input or "偷喝" in user_input:
        topic = "冰箱食物管理與尊重"
        gentle = f"{target}～不好意思，我放在冰箱的食物/飲料好像不小心被動到了耶，如果是你拿錯的話再跟我說一聲喔，謝謝！"
        group = f"【冰箱使用規範】溫馨提醒各位室友，非本人的食物與飲料請勿擅自食用。如不慎誤食，請主動向原物主告知或補償。"
        playful = f"{target}～驚爆！冰箱內發生神祕的「美味失蹤事件」，某個高熱量物質竟人間蒸發。到底是道德的淪喪還是肚子的飢餓？請拿錯的朋友主動自首！"
        
    # 情境六：公共空間堆放私人物品/客廳鞋子亂丟
    elif "客廳" in user_input or "雜物" in user_input or "鞋子" in user_input or "玄關" in user_input or "包裹" in user_input:
        topic = "公共區域雜物清理"
        gentle = f"{target}～客廳/玄關那邊好像有一些你的個人物品（如鞋子/包裹），有空的話再麻煩幫我收進房間一下，讓走路空間大一點，謝囉！"
        group = f"【公共區域公告】玄關、客廳屬於共同生活空間，請勿長期堆放個人私人物品、鞋子或未拆包裹，請今日內協助收回房內，謝謝配合。"
        playful = f"{target}～報告！公共區域已被來路不明的雜物大軍攻佔，走路都得開啟「障礙物閃避模式」。呼叫物主出動收納大法，還原這片土地的和平！"
        
    # 情境七：帶男女朋友或朋友過夜沒先說
    elif "過夜" in user_input or "帶人" in user_input or "朋友" in user_input or "留宿" in user_input:
        topic = "訪客與留宿提前報備"
        gentle = f"{target}～嗨，如果最近有朋友或另一半要來過夜的話，再麻煩提早在群組說一聲喔，這樣大家比較有心理準備，謝謝你！"
        group = f"【共居生活公約】為維護全體室友的隱私與居住安全，若有訪客前來或需留宿過夜，請務必提早於群組中報備，感謝大家的配合。"
        playful = f"{target}～大內密探回報！據說最近有神秘的新面孔出沒？下次帶高級 NPC（朋友/閃光）來過夜前記得先發全服公告，讓大家穿好衣服迎接喔！"
        
    # 情境八：冷氣/電燈/電器忘記關 (浪費電)
    elif "冷氣" in user_input or "沒關" in user_input or "浪費電" in user_input or "電燈" in user_input:
        topic = "節約能源與電器管理"
        gentle = f"{target}～嗨嗨，你出門/睡覺的時候冷氣和電燈好像忘記關了，我剛剛幫你順手關掉囉，下次出門再稍微幫我注意一下，感謝！"
        group = f"【節能減碳公告】近期電費高漲，請各位室友離開公共區域或出門前，務必確認冷氣、電燈、電扇等電器是否已完全關閉，避免資源浪費。"
        playful = f"{target}～警報！我們家正處於「台電大股東模式」，沒人的房間冷氣卻開得像北極一樣冰爽。為了大家的荷包君，出門前請務必執行關機密技！"
        
    # 情境九：金錢/催繳房租、水電費、公積金
    elif "房租" in user_input or "水電" in user_input or "催繳" in user_input or "給錢" in user_input or "欠錢" in user_input:
        topic = "共同費用與租金催繳"
        gentle = f"{target}～提醒一下，這期的房租/水電費好像還沒收到喔，如果你有空的話再麻煩轉帳給我，再跟我說一聲，謝謝你！"
        group = f"【財務催繳公告】本期共同費用（房租/水電費/公積金）已截止收費，請尚未繳交之室友於今日內完成轉帳，以利後續作業。"
        playful = f"{target}～叮咚！您的「財神爺催款通知」已上線。為了維持我們微弱的債權人信任，請盡速動動手指將款項奉上，感恩功德無量！"
        
    # 情境十：其餘沒預期到的萬用 Fallback
    else:
        # 萬用複合模板：不論是家事還是生活習慣，套進去都完美通順
        gentle = f"{target}～不好意思想稍微反映一下關於「{topic}」的事，再麻煩你抽空協助留意或處理一下，感謝！"
        group = f"【生活公約提醒】請大家共同留意「{topic}」的相關狀況，對事不對人，一起維持良好的共居品質，謝謝配合！"
        playful = f"{target}～偵測到「{topic}」的時空能量值異常！需要你動動手指施展魔法來平息它，大家正期待著你的巨星登場！"

    # 確保群組與嘴砲版沒有漏網之魚的髒話
    group = soften_for_group(group)
    playful = soften_for_group(playful)
    line_message = group

    # 5. 組裝 Markdown 回覆
    markdown = f"""
### conflict-mediator-skill：衝突調解技能

**語氣風險分析** > {risk_analysis}

**溫柔版私訊** * `{gentle}`

**群組公告版** * `{group}`

**嘴砲但不失禮版** * `{playful}`

**推薦發送策略**：先將【溫柔版】複製並私訊給 {target}；若到了約定時間仍未改善，再將【群組公告版】丟入 LINE 群組，既保留面子又能達到約束效果。
""".strip()

    return {
        "intent": "conflict_mediator",
        "skill": "conflict-mediator-skill",
        "response_markdown": markdown,
        "line_message": line_message,
        "tables": {
            "提醒版本": [
                {"版本": "溫柔版", "內容": gentle},
                {"版本": "群組公告版", "內容": group},
                {"版本": "嘴砲但不失禮版", "內容": playful},
            ]
        },
        "tools_used": ["extract_target", "extract_topic", "guardrail_check", "soften_for_group"],
        "memory_updates": [f"conflict_mediated event @ {event['timestamp']}"]
    }