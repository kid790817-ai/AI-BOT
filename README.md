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

## 群聊模組

六隻 bot 共用一個群聊頻道，人類發話時各自骰機率決定要不要回，可以互相接話。

### 機制

- 人類發話 → 開窗口，每隻 bot 骰 50% 決定是否參與
- 第一次回覆後，每則新訊息 20% 機率再回
- 第二次回覆後，5%
- 第三次後不再回
- 窗口 60 秒沒人講話自動關閉
- 只有人類訊息能開窗口，bot 訊息不會開新窗口
- 回覆前隨機延遲 2～8 秒，模擬打字

### 每隻 bot 的群聊個性

| Bot | 群聊角色 |
|-----|---------|
| Koda | 穩穩的、話少但到位、偶爾冷幽默、會扯回健康 |
| Karina | 節奏快、愛操心、會 cue 別人、氣氛推動者 |
| Mary | 安靜但有在看、碰到感興趣的會突然話多、書呆子式幽默 |
| Sharon | 反應快、講話直、愛吐槽科技圈、什麼都知道的氣場 |
| Winnie | 嘴、大姐氣場、毒蛇但在乎、不用 emoji |
| Claire | 最菜、怯怯的但會小反駁、偶爾歪到 SEO 角度、天然可愛 |

### 技術實作

- 共用模組：`group_chat.py`（每隻 bot 的 repo 根目錄各一份，邏輯相同）
- 人設檔：`group_persona.md`（每隻 bot 各自不同）
- commands.Bot（Koda、Karina、Mary、Claire）：以 Cog 載入
- discord.Client（Sharon、Winnie）：import handler 後在 on_message 呼叫

### 環境變數（Railway）

| 變數 | 說明 |
|------|------|
| `GROUP_CHANNEL_ID` | 群聊頻道 ID |
| `GROUP_AI_API_KEY` | AI API key（可共用 bot 本身的） |
| `GROUP_AI_MODEL` | 模型名稱 |
| `GROUP_AI_BASE_URL` | （選用）DeepSeek bot 才需要 |

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
- **群聊模組**：`group_chat.py`（共用邏輯）+ `group_persona.md`（各自人設）

## 更新紀錄

| 日期 | 異動 |
|------|------|
| 2025-05-30 | 新增群聊模組：六隻 bot 共用群聊頻道，機率遞減機制（50%→20%→5%→0%），各自有群聊人設。同時修正 Sharon 的 bot 過濾 bug、Winnie 新增 message_content intent |
| 2025-05-30 | 建立追蹤總覽 |