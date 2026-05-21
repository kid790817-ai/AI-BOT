"""
sharon.py
============================================================
雪倫主程式。把三條線掛在同一隻 bot 裡：

  線一　自動警報：定時掃來源 → 篩五分類 → 寫報告 → 推給你
  線二　手動問答：你在 Telegram 丟問題 → 撈相關情報 → Claude 回你
  線三　健康監控：每週檢查有沒有來源壞掉 → 壞了主動提醒你（不自動改）

排程用 python-telegram-bot 內建的 job queue，跟收發訊息共用同一個事件迴圈，
不另外接 apscheduler，避免兩個迴圈對不上、推播推不出去的坑。

部署照米蘭達：Procfile 寫 `worker: python3 sharon.py`，當背景程式一直掛著跑。
需要安裝帶 job-queue 的版本：python-telegram-bot[job-queue]

啟動前需要的環境變數（在部署平台設定，不寫進 repo）：
  SHARON_TELEGRAM_TOKEN   雪倫自己的 Telegram token（@BotFather 拿）
  ANTHROPIC_API_KEY       Claude key（跟米蘭達共用）
  SHARON_OWNER_CHAT_ID    你的 Telegram ID（選填，第一次跟雪倫講話它會印出來）
============================================================
"""

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

from sharon_config import (
    TELEGRAM_TOKEN,
    SHARON_OWNER_CHAT_ID,
    SCAN_INTERVAL_MINUTES,
    HEALTH_CHECK_INTERVAL_HOURS,
    MAX_REPORTS_PER_SCAN,
)
from sharon_fetch import scan_all_sources, load_intel, check_stale_sources
from sharon_brain import classify_item, write_report, answer_question, small_talk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("sharon")

# 全域記住老闆的 chat id（推播要用）。優先用環境變數，沒有就等第一則訊息學起來。
OWNER_CHAT_ID = int(SHARON_OWNER_CHAT_ID) if SHARON_OWNER_CHAT_ID else None


# ============================================================
# 線一：自動警報（掃描＋推播）
# ============================================================
# 注意：掃描與 Claude 呼叫是「會卡住的同步工作」，用 asyncio.to_thread
# 丟到背景線程跑，避免卡住整隻 bot 的訊息收發（照米蘭達的 to_thread 慣例）。

async def run_scan_and_alert(context: ContextTypes.DEFAULT_TYPE):
    """掃一次所有來源，把符合五分類的寫成報告推給老闆。

    這裡體現規格書的分工：
    - 「發幾則」＝程式數數（符合幾則就發幾則，這裡用程式 len 控制）
    - 「內容」＝Claude 寫
    - 五分類是篩子：沒中的不發，整批沒中就完全不出聲（警報器精神）
    """
    if OWNER_CHAT_ID is None:
        logger.warning("還不知道老闆的 chat id，跳過推播（先對雪倫講一句話讓它記住你）")
        return

    try:
        new_items = await asyncio.to_thread(scan_all_sources)
    except Exception as e:
        logger.error("掃描失敗：%s", e)
        return

    if not new_items:
        logger.info("沒有新東西，雪倫保持沉默")
        return

    # 逐則判斷分類，篩出有命中的（程式在做篩選與計數，不交給 AI 決定總量）
    qualified = []
    for item in new_items:
        cats = await asyncio.to_thread(classify_item, item)
        if cats:
            qualified.append((item, cats))

    if not qualified:
        logger.info("有新東西但都不符合五分類，雪倫保持沉默")
        return

    total = len(qualified)
    # 爆量保護：超過上限只推前幾則，其餘併進前言
    to_send = qualified[:MAX_REPORTS_PER_SCAN]
    overflow = total - len(to_send)

    # 前言（一則）
    if overflow > 0:
        preamble = (
            f"🔔 偵測到一批新發表，篩出 {total} 則符合你在意的範圍，"
            f"以下推送前 {len(to_send)} 則，其餘 {overflow} 則先省略。"
        )
    else:
        preamble = f"🔔 偵測到 {total} 則符合你在意的新消息，逐則送上。"
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=preamble)

    # 逐則報告（拆開一則一則發）
    for item, cats in to_send:
        report = await asyncio.to_thread(write_report, item, cats)
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=report)


# ============================================================
# 線三：健康監控
# ============================================================

async def run_health_check(context: ContextTypes.DEFAULT_TYPE):
    """檢查有沒有來源壞掉，壞了主動提醒老闆（不自動改網址）。"""
    if OWNER_CHAT_ID is None:
        return
    try:
        stale = await asyncio.to_thread(check_stale_sources)
    except Exception as e:
        logger.error("健康檢查失敗：%s", e)
        return

    if not stale:
        logger.info("健康檢查：所有來源正常")
        return

    lines = ["⚠️ 來源健康檢查發現異常，請確認以下來源是否需要更換："]
    for s in stale:
        if s["days_silent"] is None:
            lines.append(f"・{s['name']}：從未成功抓到東西，可能網址一開始就有問題。")
        else:
            lines.append(f"・{s['name']}：已 {s['days_silent']} 天沒有任何更新。")
    lines.append("（可能是它真的沒發，也可能是來源壞了。雪倫不會自己改，等你確認。）")
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text="\n".join(lines))


# ============================================================
# 線二：手動問答
# ============================================================

def _pick_relevant_intel(question, intel, limit=8):
    """從情報庫挑出跟問題相關的幾則，用簡單關鍵字比對。

    第一版先用樸素做法：把問題拆成關鍵字，比對標題與內容。
    日後要更聰明可以換成語意檢索，但第一版這樣夠用、零成本。
    若完全比不到，退而給最近抓到的幾則（讓雪倫至少有料可講）。
    """
    q = question.lower()
    # 抓出問題裡比較有意義的詞（長度 ≥ 2 的詞片段），樸素切分
    keywords = [w for w in q.replace("？", " ").replace("，", " ").split() if len(w) >= 2]

    scored = []
    for item in intel:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        score = sum(1 for kw in keywords if kw in text)
        # 公司名等專有名詞直接命中加重
        for name in ["openai", "google", "gemini", "claude", "anthropic", "deepseek",
                     "qwen", "kimi", "glm", "meta", "llama", "grok", "gpt"]:
            if name in q and name in text:
                score += 2
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return [item for _, item in scored[:limit]]

    # 完全沒比到，給最近抓到的幾則（情報庫尾端是最新的）
    return intel[-limit:] if intel else []


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """收到老闆的文字訊息：先判斷是閒聊還是問情報，分開處理。"""
    global OWNER_CHAT_ID

    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # 第一次講話：把老闆的 chat id 記下來（推播要用）
    if OWNER_CHAT_ID is None:
        OWNER_CHAT_ID = chat_id
        logger.info("已記住老闆的 chat id：%s（建議設成環境變數 SHARON_OWNER_CHAT_ID）", chat_id)

    if not text:
        return

    # 判斷這句是不是在問 AI 情報。判斷標準：有沒有提到任何一家公司／模型，
    # 或有沒有情報相關的關鍵字。沒有的話就當閒聊，自然回一句、不查情報庫。
    if _looks_like_intel_question(text):
        await update.message.reply_text("讓我查一下手上的情報……")
        intel = await asyncio.to_thread(load_intel)
        relevant = _pick_relevant_intel(text, intel)
        answer = await asyncio.to_thread(answer_question, text, relevant)
        await update.message.reply_text(answer)
    else:
        reply = await asyncio.to_thread(small_talk, text)
        await update.message.reply_text(reply)


# 判斷一句話是不是在問 AI 情報（提到公司／模型，或含情報關鍵字就算）
_INTEL_HINTS = [
    "openai", "google", "gemini", "claude", "anthropic", "deepseek",
    "qwen", "kimi", "glm", "meta", "llama", "grok", "gpt", "mistral",
    "模型", "api", "發表", "上線", "降價", "價格", "功能", "版本",
    "agent", "串接", "影像", "圖片", "新聞", "情報", "消息",
]


def _looks_like_intel_question(text):
    t = text.lower()
    return any(hint in t for hint in _INTEL_HINTS)


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """指令 /scan：叫雪倫立刻掃一次（不用等排程）。"""
    await update.message.reply_text("收到，馬上掃一輪……")
    await run_scan_and_alert(context)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """指令 /status：回報雪倫現在的狀態。"""
    intel = await asyncio.to_thread(load_intel)
    stale = await asyncio.to_thread(check_stale_sources)
    msg = f"雪倫運作中。\n情報庫累積：{len(intel)} 則。\n"
    if stale:
        msg += f"有 {len(stale)} 個來源可能異常，輸入 /health 看細節。"
    else:
        msg += "所有來源健康正常。"
    await update.message.reply_text(msg)


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """指令 /health：立刻跑一次健康檢查。"""
    await update.message.reply_text("檢查來源健康中……")
    await run_health_check(context)


# ============================================================
# 啟動
# ============================================================

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("SHARON_TELEGRAM_TOKEN 未設定——去 @BotFather 拿雪倫的 token")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 線二：指令與問答
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    # 線一 & 線三：用內建 job queue 排程（跟收發訊息同一個事件迴圈）
    jq = app.job_queue
    jq.run_repeating(
        run_scan_and_alert,
        interval=SCAN_INTERVAL_MINUTES * 60,
        first=10,  # 啟動 10 秒後先掃一次
        name="scan",
    )
    jq.run_repeating(
        run_health_check,
        interval=HEALTH_CHECK_INTERVAL_HOURS * 3600,
        first=HEALTH_CHECK_INTERVAL_HOURS * 3600,
        name="health",
    )

    logger.info(
        "雪倫上線：每 %d 分鐘掃一次，每 %d 小時做健康檢查。",
        SCAN_INTERVAL_MINUTES, HEALTH_CHECK_INTERVAL_HOURS,
    )

    # 開始收 Telegram 訊息（會一直卡著跑，是主迴圈）
    app.run_polling()


if __name__ == "__main__":
    main()
