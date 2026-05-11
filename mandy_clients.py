import time
import requests
import anthropic

from mandy_config import (
    ANTHROPIC_API_KEY,
    PERPLEXITY_API_KEY,
    GROK_API_KEY,
    PERPLEXITY_MODEL,
    GROK_MODEL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    CLAUDE_MAX_TOKENS,
    GROK_MAX_TOKENS,
)
from mandy_utils import MandyError


anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _post_json_with_retry(url: str, headers: dict, body: dict, label: str) -> dict:
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue

            response.raise_for_status()
            return response.json()

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue

    raise MandyError(f"{label} API 呼叫失敗：{last_error}")


def call_perplexity(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    data = _post_json_with_retry(
        "https://api.perplexity.ai/chat/completions",
        headers,
        body,
        "Perplexity",
    )

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise MandyError("Perplexity 回傳格式異常，沒有 choices[0].message.content。")


def call_claude(prompt: str, model: str) -> str:
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            chunks = []
            for block in response.content:
                text = getattr(block, "text", None)
                if text:
                    chunks.append(text)

            result = "\n".join(chunks).strip()
            if not result:
                raise MandyError("Claude 回傳空內容。")
            return result

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue

    raise MandyError(f"Claude API 呼叫失敗：{last_error}")


def call_grok(prompt: str) -> str:
    if not GROK_API_KEY:
        raise MandyError("未設定 GROK_API_KEY，跳過 Grok。")

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": GROK_MAX_TOKENS,
    }

    data = _post_json_with_retry(
        "https://api.x.ai/v1/chat/completions",
        headers,
        body,
        "Grok",
    )

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise MandyError("Grok 回傳格式異常，沒有 choices[0].message.content。")
