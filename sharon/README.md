# 雪倫　AI 情報警報器

一隻盯死特定 AI 來源、平常沉默、只在「真的有新發表」時才出聲的情報警報器。透過 Telegram 推送，也能回答你的提問。

設計理念詳見 `SPEC.md`。

## 它會做三件事

一、自動警報：定時掃所有來源，篩出符合五分類的新消息，寫成白話報告推給你。平常沒東西就閉嘴。

二、回答提問：你在 Telegram 丟問題（例如「你怎麼看這次 Google 發表的」「裡面有適合串 API 的模型嗎」），它根據抓到的情報回你。

三、健康監控：每週檢查有沒有來源壞掉，壞了主動提醒你，但不會自己改網址，等你確認。

## 檔案結構

```
sharon/
├── sharon.py          主程式（掛起三條線）
├── sharon_config.py   設定中樞（token、來源清單、參數）
├── sharon_fetch.py    抓資料（掃 RSS／GitHub、存情報庫）
├── sharon_brain.py    串 Claude（篩分類、寫報告、回答提問）
├── requirements.txt   套件清單
└── SPEC.md            設計規格書
```

## 啟動前要設定的環境變數

| 變數 | 必填 | 說明 |
|---|---|---|
| `SHARON_TELEGRAM_TOKEN` | 是 | 雪倫自己的 Telegram token，去 @BotFather 拿，跟米蘭達分開 |
| `ANTHROPIC_API_KEY` | 是 | Claude key，跟米蘭達共用同一把 |
| `SHARON_OWNER_CHAT_ID` | 否 | 你的 Telegram ID。沒設的話，第一次對雪倫講話它會把你的 ID 印在 log 裡，之後設進去即可 |
| `GITHUB_TOKEN` | 否 | 抓中國大廠 GitHub release 用。不設也能跑，但有速率限制，撞到再加 |

可調參數（都有預設值，不設也能跑）：

| 變數 | 預設 | 說明 |
|---|---|---|
| `SHARON_SCAN_INTERVAL` | 60 | 每隔幾分鐘掃一次 |
| `SHARON_HEALTH_INTERVAL` | 168 | 每隔幾小時做健康檢查（168＝一週） |
| `SHARON_STALE_DAYS` | 14 | 來源幾天沒更新就提醒 |
| `SHARON_MAX_REPORTS` | 5 | 單次最多推幾則（爆量保護） |

## 怎麼跑

本機測試：

```bash
pip install -r requirements.txt
export SHARON_TELEGRAM_TOKEN=你的token
export ANTHROPIC_API_KEY=你的key
python3 sharon.py
```

部署（照米蘭達的方式，當背景 worker 一直掛著跑）：

```
worker: python3 sharon.py
```

## Telegram 指令

| 指令 | 作用 |
|---|---|
| 直接打字 | 當成提問，雪倫根據情報庫回答 |
| `/scan` | 叫雪倫立刻掃一輪，不用等排程 |
| `/status` | 看雪倫現在狀態、情報庫累積幾則 |
| `/health` | 立刻跑一次來源健康檢查 |

## 第一版的已知限制

- 問答的情報撈取用的是樸素關鍵字比對，夠用但不夠聰明。日後要更準可以換成語意檢索。
- 中國大廠目前盯 GitHub release，會漏掉「發了部落格但還沒打 tag」的消息（詳見 SPEC.md）。
- 標 ⚠️ 的來源（二手代抓、The Batch）接上去前建議先實際打開確認還活著。
