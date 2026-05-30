# 🤖 AI Bot 追蹤總覽

所有 Discord Bot 的中央追蹤站。

## Bot 一覽

| Bot | 功能定位 | Repo | 部署平台 | 狀態 |
|-----|---------|------|---------|------|
| **Koda** 🐾 | 健康管理夥伴 | [Koda](https://github.com/kid790817-ai/Koda) | Railway | ✅ 上線中 |
| **Karina** 🎀 | 個人秘書 | [Karina](https://github.com/kid790817-ai/Karina) | Railway | ✅ 上線中 |
| **Claire** 🔍 | SEO 助手 | [claire-seo-bot](https://github.com/kid790817-ai/claire-seo-bot) | Railway | 🚧 開發中 |
| **Mary** 🎓 | 內容追蹤推送 | [mary](https://github.com/kid790817-ai/mary) | Railway | ✅ 上線中 |
| **Sharon** 📡 | AI 情報警報器 | [sharon](https://github.com/kid790817-ai/sharon) | Railway | ✅ 上線中 |
| **Winnie** 📈 | 投資學習助手 | [winnie](https://github.com/kid790817-ai/winnie) | Railway | ✅ 上線中 |

## 各 Bot 詳細資訊

### Koda 🐾 — 健康管理夥伴

- **功能**：體測紀錄（拍照辨識）、飲食紀錄、運動紀錄、喝水提醒、體測提醒
- **技術棧**：Python、discord.py、Anthropic API
- **排程**：喝水提醒 12:00/15:00/18:00/21:00、體測提醒每週日 21:00
- **儲存**：Railway Volume（`/data`）

### Karina 🎀 — 個人秘書

- **功能**：多帳戶記帳、自然語言提醒、每日早安報（天氣＋新聞＋行程）、Google Calendar 管理、Spotify 播放控制
- **技術棧**：Python、discord.py、Anthropic API、OpenWeatherMap、NewsAPI、Google Calendar API、Spotify API
- **排程**：每日 10:00 早安推送
- **儲存**：Railway Volume（`/data`）

### Claire 🔍 — SEO 助手

- **功能**：每週 SEO 健檢報告（PDF）、互動式討論修改方案、自動推送更新到 WordPress/Ghost、Google 索引提交、排名追蹤
- **技術棧**：Python、discord.py、Anthropic API（Haiku＋Sonnet）、Google Search Console API、Google Indexing API、Google Drive API
- **開發狀態**：Phase 1 基礎版開發中
- **儲存**：PostgreSQL / SQLite

### Mary 🎓 — 內容追蹤推送

- **功能**：追蹤 21 位國外創作者（YouTube 12 人、Podcast 4 人、文字 5 人），每日生成中文摘要推送，可展開長版濃縮
- **技術棧**：Python、discord.py、DeepSeek API、xAI Grok API、youtube-transcript-api、SQLite
- **排程**：22:00 掃描、23:00 推送（台北時間）
- **儲存**：SQLite（Railway Volume `/data`）

### Sharon 📡 — AI 情報警報器

- **功能**：每日掃描 12 個 RSS 來源、embed 摘要卡片＋深入了解按鈕、問答（情報庫＋上網查）、每週週報、議題追蹤
- **技術棧**：Python、discord.py、Anthropic API、Google Search API
- **排程**：每日 12:00 掃描、每週日 10:00 週報
- **儲存**：Railway Volume

### Winnie 📈 — 投資學習助手

- **功能**：台股日報、美股日報、Winnie 週報、投資問答
- **技術棧**：Python、discord.py、DeepSeek V4-Pro、Perplexity Sonar、FinMind、yfinance、APScheduler
- **排程**：台股日報 週一至週五 14:00、美股日報 週二至週六 08:00、週報 週日 10:00
- **儲存**：Railway Volume

## 共用技術

- **語言**：Python
- **框架**：discord.py
- **部署**：Railway（GitHub 連結自動部署）
- **AI**：Anthropic API（Koda、Karina、Claire、Sharon）、DeepSeek（Mary、Winnie）
- **儲存**：Railway Volume + SQLite

## 更新紀錄

| 日期 | 異動 |
|------|------|
| 2026-05-30 | 建立追蹤總覽 |
