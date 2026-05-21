"""
sharon_brain.py
============================================================
雪倫的腦。所有需要動用 Claude 的事都在這。

照米蘭達 miranda_llm.py 的寫法簡化：集中管理 API 呼叫、retry、錯誤處理。
雪倫只用一隻模型（Sonnet 4.6），所以比米蘭達單純很多。

三個工作：
1. classify_item()  — 判斷一則消息符不符合五分類（這步用 AI 輔助判斷，
                       但「發幾則」仍是程式數數，AI 只負責判斷單則的分類歸屬）
2. write_report()   — 把一則消息寫成詳細白話的報告
3. answer_question()— 根據情報庫回答你的提問

設計原則（呼應規格書）：
- AI 只負責「寫字」與「判斷單則屬於哪一類」。
- 「總共發幾則」「要不要發」是 sharon_main 用程式規則決定，不交給 AI。
============================================================
"""

import json
import logging
import re
import time

from sharon_config import (
    ANTHROPIC_API_KEY,
    SONNET_MODEL,
    REPORT_MAX_TOKENS,
    ANSWER_MAX_TOKENS,
    CATEGORIES,
)

logger = logging.getLogger("sharon.brain")


# ============================================================
# Claude client（照米蘭達寫法）
# ============================================================

claude = None
try:
    if ANTHROPIC_API_KEY:
        import anthropic
        claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
except ImportError:
    logger.warning("anthropic 套件未安裝，雪倫的腦無法運作")
except Exception as e:
    logger.warning("Claude client 初始化失敗：%s", e)


def _sonnet(prompt, max_tokens, max_retries=3):
    """呼叫 Sonnet 的共用入口，含限流重試（照米蘭達 retry 邏輯簡化）。"""
    if claude is None:
        raise Exception("Claude client 未初始化——檢查 ANTHROPIC_API_KEY 和 anthropic 套件")

    last_err = None
    for attempt in range(max_retries):
        try:
            resp = claude.messages.create(
                model=SONNET_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except Exception as e:
            last_err = e
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "500", "502", "503", "529"]):
                wait = 5 * (attempt + 1)
                logger.warning("Sonnet 錯誤（%s），等 %d 秒重試（%d/%d）", e, wait, attempt + 1, max_retries)
                time.sleep(wait)
                continue
            raise
    if last_err:
        raise last_err
    raise Exception("Sonnet 重試耗盡")


# ============================================================
# 1. 判斷一則消息屬於哪些分類
# ============================================================

def classify_item(item):
    """判斷一則消息符合五分類中的哪幾類。

    回傳符合的分類 list（可能多類，可能空 list）。
    空 list ＝ 不符合任何一類 ＝ 不該推（這是篩子，沒中就不發）。

    一個公告就算同時符合多類，也只回傳那幾類，由 sharon_main 發成「一則、標註跨哪幾類」。
    """
    cat_lines = "\n".join(f"{i+1}. {c}" for i, c in enumerate(CATEGORIES))
    prompt = f"""你是 AI 情報分類器。下面有一則消息，請判斷它符合以下五個分類中的哪幾類。

五個分類：
{cat_lines}

判斷原則：
- 這是「篩子」不是「配額」。不符合任何一類就回空陣列，不要勉強塞。
- 寧可嚴格。只有真的講到該分類的實質內容才算，沾到邊不算。
- 一則可以同時符合多類。

消息：
標題：{item.get('title', '')}
內容：{item.get('summary', '')[:1500]}

只輸出 JSON，不要任何其他文字，格式如下：
{{"categories": ["符合的分類名稱", ...]}}

分類名稱必須完全照上面五個的文字。不符合就回 {{"categories": []}}。"""

    try:
        raw = _sonnet(prompt, max_tokens=200)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            return []
        result = json.loads(match.group())
        cats = result.get("categories", [])
        # 只保留合法分類名稱
        return [c for c in cats if c in CATEGORIES]
    except Exception as e:
        logger.warning("分類失敗，當作不符合：%s", e)
        return []


# ============================================================
# 2. 把一則消息寫成詳細白話報告
# ============================================================

def write_report(item, categories):
    """把一則消息寫成一則詳細、白話的報告。

    格式照規格書：標題 → 重點（詳細白話）→ 為什麼值得看 → 原文連結。
    categories 是這則命中的分類，會標註在報告裡。
    """
    cat_str = "、".join(categories)
    prompt = f"""你是 AI 情報分析員雪倫。把下面這則消息寫成一則給老闆看的情報報告。

要求：
- 用繁體中文，白話講清楚，不要堆術語。不確定對方懂不懂，就用最直白的講法。
- 內容要詳細，講清楚這到底是什麼、有什麼變化。
- 最後說明「為什麼值得看」，點出對實際應用（特別是串 API、做產品）的意義。
- 所有標點符號一律使用全形，嚴禁半形逗號句號括號等。
- 不要客套、不要開場白，直接進入內容。

消息原始資料：
標題：{item.get('title', '')}
內容：{item.get('summary', '')[:2000]}
來源：{item.get('source', '')}
原文連結：{item.get('link', '')}

這則命中的分類：{cat_str}

請照這個結構輸出（用全形標點）：

【標題】
（用一句話總結這則消息）

【重點】
（詳細白話講清楚這件事）

【為什麼值得看】
（點出實際意義）

【分類】{cat_str}
【原文】{item.get('link', '')}"""

    try:
        return _sonnet(prompt, max_tokens=REPORT_MAX_TOKENS)
    except Exception as e:
        logger.error("寫報告失敗：%s", e)
        # 寫不出來至少給原始標題加連結，不要整則消失
        return f"【標題】{item.get('title', '')}\n【原文】{item.get('link', '')}\n（報告生成失敗，附原始資訊）"


# ============================================================
# 3. 根據情報庫回答你的提問
# ============================================================

def answer_question(question, relevant_items):
    """根據撈出來的相關情報，回答老闆的提問。

    relevant_items 是 sharon_main 從情報庫挑出來、跟問題相關的幾則。
    雪倫只根據這些料回答，不憑空瞎掰。
    """
    if not relevant_items:
        return "我手上的情報庫裡沒有跟這個問題相關的東西。可能是還沒抓到，或這不在我盯的來源範圍內。"

    intel_text = ""
    for i, item in enumerate(relevant_items, 1):
        intel_text += f"""
[情報 {i}]
標題：{item.get('title', '')}
內容：{item.get('summary', '')[:1500]}
來源：{item.get('source', '')}
連結：{item.get('link', '')}
"""

    prompt = f"""你是 AI 情報分析員雪倫。老闆問你一個問題，請根據下面這些你手上抓到的情報來回答。

回答要求：
- 用繁體中文，白話、直接，不要堆術語。
- 有結論先說結論，不要鋪陳，不要客套。
- 只根據下面提供的情報回答。如果情報不足以回答，就老實說「目前手上的料不夠回答這個」，不要瞎掰。
- 如果老闆問的是「適不適合串 API」這類實用判斷，就針對 API、價格、可用性這些面向具體分析。
- 所有標點符號一律使用全形，嚴禁半形。

老闆的問題：
{question}

你手上的相關情報：
{intel_text}

請直接回答（用全形標點）："""

    try:
        return _sonnet(prompt, max_tokens=ANSWER_MAX_TOKENS)
    except Exception as e:
        logger.error("回答問題失敗：%s", e)
        return f"回答時出錯了：{e}"
