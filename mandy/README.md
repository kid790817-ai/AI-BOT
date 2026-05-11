# Mandy v2

Mandy 是單頻道電影文章產生 Discord bot。

## 使用方式

只接受兩種主要指令：

```text
觀影前 片名
影評 片名
```

輔助指令：

```text
狀態
取消
重跑
```

## 輸出檔案

每次任務會輸出：

```text
01_research
02_angle_plan
03_article_structure
04_final_article
05_seo_pack
```

最重要的是：

```text
04_final_article
05_seo_pack
```

## 環境變數

必要：

```text
DISCORD_TOKEN
ANTHROPIC_API_KEY
PERPLEXITY_API_KEY
```

選用：

```text
GROK_API_KEY
MANDY_USE_GROK_SECOND_OPINION=true
MANDY_PERPLEXITY_MODEL=sonar-pro
MANDY_CLAUDE_MAIN_MODEL=claude-sonnet-4-20250514
MANDY_CLAUDE_REVIEW_MODEL=claude-sonnet-4-20250514
MANDY_GROK_MODEL=grok-3
MANDY_REQUEST_TIMEOUT=180
MANDY_MAX_RETRIES=2
MANDY_CLAUDE_MAX_TOKENS=12000
MANDY_GROK_MAX_TOKENS=12000
```

## 注意

SEO Pack 不包含：

```text
OG Title
OG Description
```

因為目前需求用不到。
