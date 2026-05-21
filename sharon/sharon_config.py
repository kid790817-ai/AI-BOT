"""
sharon_config.py
============================================================
雪倫設定中樞。所有 token、API key、來源清單、參數都在這。

設計原則（照米蘭達的慣例）：
- 敏感資訊（token、key）一律走環境變數，不寫死在程式裡，不進 repo。
- 來源清單集中管理，要加減來源只動這個檔。
- 模型字串、門檻值都拉成常數，方便日後微調。
============================================================
"""

import os

# ============================================================
# 敏感資訊（走環境變數，部署時在平台設定，不寫進 repo）
# ============================================================

# 雪倫自己的 Telegram bot token（去 @BotFather 拿，跟米蘭達分開）
TELEGRAM_TOKEN = os.environ.get("SHARON_TELEGRAM_TOKEN", "")

# 你的 Telegram 使用者 ID（雪倫只跟你一個人講話，自動推播也推給你）
# 不知道自己的 ID 的話，第一次跑起來對雪倫打任何字，它會把你的 ID 印在 log 裡
SHARON_OWNER_CHAT_ID = os.environ.get("SHARON_OWNER_CHAT_ID", "")

# Claude API key（跟米蘭達共用同一把，沿用既有環境變數名）
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ============================================================
# 模型設定
# ============================================================

# 雪倫寫報告、回答問題都用 Sonnet 4.6（規格書已定案）
SONNET_MODEL = "claude-sonnet-4-6"

# 寫一則情報報告的長度上限
REPORT_MAX_TOKENS = 1200

# 回答你提問的長度上限
ANSWER_MAX_TOKENS = 1500


# ============================================================
# 排程設定
# ============================================================

# 每隔幾分鐘自動掃一次所有來源
SCAN_INTERVAL_MINUTES = int(os.environ.get("SHARON_SCAN_INTERVAL", "60"))

# 來源健康監控：每隔幾小時檢查一次有沒有來源壞掉
HEALTH_CHECK_INTERVAL_HOURS = int(os.environ.get("SHARON_HEALTH_INTERVAL", "168"))  # 168 小時＝一週

# 某來源連續幾天沒任何更新，就發提醒（規格書建議初版 14 天）
SOURCE_STALE_DAYS = int(os.environ.get("SHARON_STALE_DAYS", "14"))

# 單次掃描最多推幾則（爆量保護，其餘併進前言）
MAX_REPORTS_PER_SCAN = int(os.environ.get("SHARON_MAX_REPORTS", "5"))


# ============================================================
# 資料儲存
# ============================================================

# 抓到的東西存哪（含已推播與未推播的全部，供你日後問答查詢）
DATA_DIR = os.environ.get("SHARON_DATA_DIR", "sharon_data")

# 已經看過的項目記錄檔（避免重複推播同一則）
SEEN_FILE = os.path.join(DATA_DIR, "seen.json")

# 抓到的情報庫（全部留著，問答時查這個）
INTEL_FILE = os.path.join(DATA_DIR, "intel.json")

# 每個來源「上次成功抓到東西的時間」（健康監控用）
SOURCE_HEALTH_FILE = os.path.join(DATA_DIR, "source_health.json")


# ============================================================
# 五分類篩選（規格書核心：這是篩子，不是配額）
# ============================================================

CATEGORIES = [
    "新模型與功能",
    "API 相關資訊",
    "圖片／影像功能",
    "價格與可用性",
    "agent 與工具串接能力",
]


# ============================================================
# 來源清單（2026 年 5 月體檢後的修訂版，詳見 SPEC.md 第四節）
# ============================================================
# type 說明：
#   rss    — 標準 RSS／Atom feed，用 feedparser 直接抓
#   github_releases — 盯某個 GitHub 帳號／組織的 release
#
# tier 只是分類標籤，方便你日後辨識，程式不靠它做事。

SOURCES = [
    # ── 美國大廠 ──
    {
        "name": "OpenAI",
        "type": "rss",
        "url": "https://openai.com/news/rss.xml",
        "tier": "美國大廠",
        "note": "官方原生",
    },
    {
        "name": "Anthropic",
        "type": "rss",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "tier": "美國大廠",
        "note": "二手代抓（Olshansk），無官方原生 RSS",
    },
    {
        "name": "Google AI",
        "type": "rss",
        "url": "https://blog.google/technology/ai/rss/",
        "tier": "美國大廠",
        "note": "官方原生",
    },
    {
        "name": "Google DeepMind",
        "type": "rss",
        "url": "https://deepmind.google/blog/rss.xml",
        "tier": "美國大廠",
        "note": "官方原生",
    },
    {
        "name": "Meta AI",
        "type": "rss",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_meta_ai.xml",
        "tier": "美國大廠",
        "note": "二手代抓（Olshansk）",
    },
    {
        "name": "xAI",
        "type": "rss",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_xai_news.xml",
        "tier": "美國大廠",
        "note": "二手代抓，接前確認此 feed 仍在生成",
    },

    # ── 中國大廠（走 GitHub，公告多在微信抓不到）──
    {
        "name": "DeepSeek",
        "type": "github_releases",
        "url": "deepseek-ai",
        "tier": "中國大廠",
        "note": "盯整個組織的 release。注意 release 不等於發表，可能漏",
    },
    {
        "name": "阿里 Qwen",
        "type": "github_releases",
        "url": "QwenLM",
        "tier": "中國大廠",
        "note": "舊部落格 qwenlm.github.io 已停更，主來源轉 qwen.ai/research，此處先盯 GitHub",
    },
    {
        "name": "月之暗面 Kimi",
        "type": "github_releases",
        "url": "MoonshotAI",
        "tier": "中國大廠",
        "note": "新版都在這發",
    },
    {
        "name": "智譜 GLM",
        "type": "github_releases",
        "url": "zai-org",
        "tier": "中國大廠",
        "note": "已從 THUDM 搬到 zai-org，舊帳號只剩研究 repo",
    },

    # ── 媒體深度層 ──
    {
        "name": "MIT Tech Review（MIT News AI）",
        "type": "rss",
        "url": "https://news.mit.edu/rss/topic/artificial-intelligence2",
        "tier": "媒體",
        "note": "官方原生",
    },
    {
        "name": "The Batch（deeplearning.ai）",
        "type": "rss",
        "url": "https://www.deeplearning.ai/the-batch/feed/",
        "tier": "媒體",
        "note": "接前確認此原生 feed 仍在；週更，健康監控門檻要放寬",
    },
]
