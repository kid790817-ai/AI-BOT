import os

# ─────────────────────────────────────────
# Mandy Bot 設定
# ─────────────────────────────────────────

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
PERPLEXITY_API_KEY = os.environ["PERPLEXITY_API_KEY"]
GROK_API_KEY = os.environ.get("GROK_API_KEY", "")

# 預設模型
PERPLEXITY_MODEL = os.getenv("MANDY_PERPLEXITY_MODEL", "sonar-pro")
CLAUDE_MAIN_MODEL = os.getenv("MANDY_CLAUDE_MAIN_MODEL", "claude-sonnet-4-20250514")
CLAUDE_REVIEW_MODEL = os.getenv("MANDY_CLAUDE_REVIEW_MODEL", "claude-sonnet-4-20250514")
GROK_MODEL = os.getenv("MANDY_GROK_MODEL", "grok-3")

# API 參數
REQUEST_TIMEOUT = int(os.getenv("MANDY_REQUEST_TIMEOUT", "180"))
MAX_RETRIES = int(os.getenv("MANDY_MAX_RETRIES", "2"))
CLAUDE_MAX_TOKENS = int(os.getenv("MANDY_CLAUDE_MAX_TOKENS", "12000"))
GROK_MAX_TOKENS = int(os.getenv("MANDY_GROK_MAX_TOKENS", "12000"))

# 單頻道使用：同一時間只允許一個任務
ALLOW_ONE_ACTIVE_TASK = True

# 是否使用 Grok 做第二意見。
# 如果沒設 GROK_API_KEY，會自動跳過。
USE_GROK_SECOND_OPINION = os.getenv("MANDY_USE_GROK_SECOND_OPINION", "true").lower() == "true"

# 輸出檔案前綴
OUTPUT_PREFIXES = {
    "research": "01_research",
    "angle_plan": "02_angle_plan",
    "structure": "03_article_structure",
    "final_article": "04_final_article",
    "seo_pack": "05_seo_pack",
}
