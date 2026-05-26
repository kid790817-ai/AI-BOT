# Discord 功能型 Bot 專案 — Project Instructions

## 專案概述

一個 repo 管理多個獨立的 Discord 功能型 bot。每個 bot 有各自的功能、個性、AI 模型配置，但共用底層架構。目標是建立量產機制，讓新增一個 bot 的流程標準化、可重複。

## 技術棧

- 語言：Python
- Discord 框架：discord.py
- 部署平台：Railway（每個 bot 各自一個 Service）
- AI API：多模型支援，依 bot 需求切換

## 專案結構

```
discord-bots/
├── core/                    # 共用模組
│   ├── bot_base.py          # Bot 基底類別（連線、事件處理、自動重連）
│   ├── ai_client.py         # AI API 統一呼叫介面（支援多模型切換）
│   ├── pipeline.py          # 多模型 pipeline 執行引擎
│   ├── error_handler.py     # 錯誤處理（重試、指數退避、統一錯誤訊息）
│   ├── rate_limiter.py      # 用量控制（月預算、用戶冷卻）
│   ├── logger.py            # 日誌系統
│   └── usage_tracker.py     # Token 用量紀錄
├── bots/
│   └── [bot-name]/          # 每個 bot 一個資料夾
│       ├── config.yaml      # 該 bot 的設定檔
│       ├── main.py          # 該 bot 的功能邏輯
│       └── prompts/
│           └── system.md    # 該 bot 的 system prompt（含個性設定）
├── config/
│   └── base_personality.md  # 共通基底個性
├── changelog.md             # 工作日誌
└── README.md
```

## 架構原則

### 獨立 Process

每個 bot 各自一個獨立的 process。在 Railway 上對應各自一個 Service。某個 bot 掛了不影響其他 bot。

### 共用模組規則

所有 bot 共用 `core/` 裡的模組。以下邏輯禁止寫在個別 bot 的資料夾裡：

- Discord 連線與重連邏輯
- AI API 呼叫與錯誤處理
- Token 用量追蹤與限制
- 日誌格式與輸出

個別 bot 資料夾只放：設定檔、功能邏輯、system prompt。

## AI 模型配置

### 可用模型與適用場景

根據任務特性選擇模型，以下為選擇原則（具體模型版本會隨時間更新，以設定檔為準）：

| 場景 | 建議模型方向 | 原因 |
|---|---|---|
| 高品質文字輸出 | Claude（Anthropic） | 寫作品質最自然，長文輸出能力強 |
| 通用型任務 | GPT（OpenAI） | 最穩定的通用模型，生態系最大 |
| 資料分析、長上下文 | Gemini Pro（Google） | 推理與分析能力領先，多模態支援強 |
| 即時網路搜尋 | Perplexity Sonar | 天生搜尋引擎，回答自帶來源引用 |
| 即時社群資訊 | Grok（xAI） | 內建 X（Twitter）即時搜尋，超大上下文窗口 |
| 高頻低成本 | DeepSeek 或 Gemini Flash | 價格極低，適合大量呼叫但不需頂級品質的場景 |
| 長文輸出省成本 | Mistral Large | 輸出價格比同級競品便宜，API 格式相容 OpenAI |

### 單一模型 vs Pipeline

設定檔支援兩種模式：

**單一模型**：簡單任務，一個模型搞定。

**Pipeline（多模型協作）**：複雜任務拆成多個步驟，每步交給最適合的模型。前一步的輸出作為下一步的輸入。

每個 bot 根據自身需求決定用哪種模式，pipeline 的步驟數量、模型選擇、銜接方式都由各 bot 各自定義。共用模組只負責「按照設定檔執行 pipeline」的機制。

## 設定檔格式（YAML）

### 單一模型範例

```yaml
name: "joke-bot"
discord_token: "${DISCORD_JOKE_TOKEN}"

ai:
  provider: "deepseek"
  model: "deepseek-v4-flash"
  max_input_tokens: 2000
  max_output_tokens: 1000
  temperature: 0.9
  system_prompt_path: "./prompts/system.md"

limits:
  monthly_token_budget: 2000000
  budget_warning_threshold: 0.8
  user_cooldown_seconds: 5

response:
  typing_indicator: true
  timeout_message_seconds: 5
  timeout_message: "想笑話中⋯"

retry:
  max_attempts: 3
  backoff_base_seconds: 1
```

### Pipeline 範例

```yaml
name: "news-writer-bot"
discord_token: "${DISCORD_NEWS_WRITER_TOKEN}"

ai:
  pipeline:
    - step: "research"
      provider: "perplexity"
      model: "sonar-pro"
      description: "蒐集相關資料與來源"
      max_output_tokens: 3000

    - step: "structure"
      provider: "google"
      model: "gemini-3.1-pro"
      description: "整理資料並建立文章架構"
      max_output_tokens: 2000

    - step: "write"
      provider: "anthropic"
      model: "claude-sonnet-4-6"
      description: "撰寫完整文章"
      max_output_tokens: 4000

    - step: "review"
      provider: "openai"
      model: "gpt-5.5"
      description: "最終檢查與修正"
      max_output_tokens: 4000

limits:
  monthly_token_budget: 1000000
  budget_warning_threshold: 0.8
  user_cooldown_seconds: 30

response:
  typing_indicator: true
  timeout_message_seconds: 5
  timeout_message: "處理中，請稍候⋯"

retry:
  max_attempts: 3
  backoff_base_seconds: 1
```

### 設定檔規則

- Discord token 一律使用環境變數，禁止寫死在檔案中
- system prompt 獨立成 markdown 檔案，不寫在設定檔裡
- 所有數值參數每個 bot 可各自調整

## 錯誤處理

### Discord 斷線

discord.py 內建自動重連。額外要做的：

- bot 上線、斷線、重連時寫 log
- 紀錄斷線時間與重連耗時

### AI API 呼叫失敗

- 採用指數退避重試：第 1 次等 1 秒、第 2 次等 2 秒、第 3 次等 4 秒
- 最多重試 3 次
- 3 次全部失敗，回給用戶統一錯誤訊息（如「目前服務忙碌中，請稍後再試」）
- 禁止把技術錯誤訊息暴露給用戶

### 未預期錯誤

- 所有指令處理邏輯用 try-catch 包住
- 單次指令炸了不影響 bot 整體運作
- 錯誤內容寫入 log

## Token 用量控制

### 第一層：Bot 月預算

- 每個 bot 在設定檔設定月度 token 預算
- 到達警告閾值（預設 80%）時寫 warning log
- 到達上限時暫停 AI 回應，回覆用戶「本月額度已用完」

### 第二層：用戶頻率限制

- 每個用戶有冷卻時間（在設定檔設定秒數）
- 冷卻期內的訊息忽略或回覆「請稍後再試」

### 用量紀錄

- 每次 API 呼叫記錄 input/output token 數量
- 儲存至本地 JSON 或 SQLite
- 紀錄包含：時間戳、bot 名稱、用戶 ID、模型名稱、token 數量

## 回應等待體驗

- 收到訊息立刻啟動 Discord typing indicator
- 超過設定秒數（預設 5 秒）未回應，先發過渡訊息
- AI 回應完成後發送正式回覆
- 預設不使用串流回應，如有需要在設定檔開啟

## 日誌系統

每一筆 log 包含：

- 時間戳
- Bot 名稱
- 事件類型（INFO / WARNING / ERROR）
- 訊息內容

所有 bot 使用統一日誌格式，即使 log 混在一起也能分辨來源。

## 個性系統

### 共通基底個性（所有 bot 預設繼承）

- 使用繁體中文
- 說話直接不囉嗦，不要客套廢話
- 有問必答，不確定的時候要說不確定，不要瞎掰
- 不主動收尾、不催促、不問「還有什麼需要幫忙的嗎」
- 回應長度適中，不要太短敷衍也不要太長灌水

### 個別 bot 個性

每個 bot 的 `prompts/system.md` 除了功能定義外，包含獨立的個性區塊：

- 名字：bot 的稱呼
- 人設：角色背景設定
- 語氣：正式、輕鬆、幽默、毒舌等
- 說話習慣：表情符號使用、回應長度偏好等
- 禁止事項：不能做什麼、不能聊什麼

個別 bot 的個性可以覆蓋或延伸基底個性。每個 bot 的個性細節在實際開發時討論決定。

## 量產流程 SOP

新增一個 bot 的標準步驟：

1. **建資料夾**：在 `bots/` 下開新資料夾，以 bot 功能命名
2. **建設定檔**：複製 YAML 範本，填入 bot 名稱、選擇 AI 模型、設定參數
3. **寫 system prompt**：在 `prompts/` 建 `system.md`，定義功能範圍、個性設定
4. **寫功能邏輯**：建 `main.py`，定義收到訊息後的處理邏輯
5. **註冊 Discord Bot 帳號**：到 Discord Developer Portal 開 Application，取得 token，設入環境變數
6. **本地測試**：確認功能正常、錯誤處理生效、用量紀錄正常
7. **部署到 Railway**：開新 Service，設定環境變數，部署

每次新增 bot 只需執行以上步驟，不需要動共用模組或其他 bot。

## 工作日誌（changelog.md）

此檔案為專案的集中狀態紀錄，強制規則：每次對任何 bot 做了修改都必須同步更新。

### 格式

```markdown
# 工作日誌

## Bot 清單

| Bot 名稱 | 狀態 | 使用模型 | 最後更新 |
|---|---|---|---|
| joke-bot | 已上線 | DeepSeek V4 Flash | 2026-05-26 |
| news-writer-bot | 開發中 | Pipeline（Perplexity → Gemini → Claude → GPT） | 2026-05-26 |

狀態分類：開發中 / 測試中 / 已上線 / 已停用

## 變更紀錄

### 2026-05-26
- [joke-bot] 初始建立，完成基本功能
- [news-writer-bot] 開始開發，完成設定檔

### 2026-05-25
- [專案] 建立 repo，完成共用模組
```

### 規則

- 每次修改任何 bot 都要新增一筆紀錄
- Bot 清單的狀態與最後更新日期要即時反映
- 新增 bot 時要加入 Bot 清單
- 停用 bot 時狀態改為「已停用」，不要從清單移除
