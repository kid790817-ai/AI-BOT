"""
sharon_fetch.py
============================================================
雪倫的眼睛。負責去掃所有來源、把新東西抓回來。

這個檔全是寫死的程式邏輯，不碰 AI（呼應規格書「讓 AI 寫字，不要讓 AI 做主」）：
- 抓 RSS：用 feedparser
- 抓 GitHub release：用 GitHub 公開 API
- 記住看過哪些（避免重複推）
- 把抓到的全部存進情報庫（含沒推播的，供日後問答查詢）
- 更新每個來源「上次成功抓到東西的時間」（健康監控用）

對外提供：
- scan_all_sources() → 回傳這次新抓到的項目 list
- load_intel() → 讀出整個情報庫（問答時用）
- check_stale_sources() → 回傳超過 N 天沒更新的來源 list
============================================================
"""

import json
import logging
import os
from datetime import datetime, timezone

import feedparser
import requests

from sharon_config import (
    SOURCES,
    DATA_DIR,
    SEEN_FILE,
    INTEL_FILE,
    SOURCE_HEALTH_FILE,
    SOURCE_STALE_DAYS,
)

logger = logging.getLogger("sharon.fetch")


# ============================================================
# 小工具：讀寫 JSON 檔（存在就讀，不存在就回預設）
# ============================================================

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save_json(path, data):
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 抓單一來源
# ============================================================

def _fetch_rss(source):
    """抓一個標準 RSS／Atom feed，回傳項目 list。"""
    items = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries:
            uid = entry.get("id") or entry.get("link") or entry.get("title", "")
            items.append({
                "source": source["name"],
                "uid": uid,
                "title": entry.get("title", "（無標題）"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", entry.get("updated", "")),
                "fetched_at": _now_iso(),
            })
    except Exception as e:
        logger.warning("抓 RSS 失敗 %s：%s", source["name"], e)
    return items


def _fetch_github_releases(source):
    """盯一個 GitHub 帳號／組織底下所有 repo 的最新 release。

    用 GitHub 公開 API 列出該組織的 repo，再逐一拿最新 release。
    沒帶 token 的話有速率限制（每小時 60 次），來源不多時夠用。
    若日後撞限流，可在環境變數加 GITHUB_TOKEN 提高額度。
    """
    items = []
    org = source["url"]
    gh_token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    try:
        # 列出組織底下、最近有動靜的 repo（依 push 時間排序，只看前 30 個夠了）
        repos_resp = requests.get(
            f"https://api.github.com/orgs/{org}/repos",
            headers=headers,
            params={"sort": "pushed", "per_page": 30},
            timeout=30,
        )
        # 有些是個人帳號不是組織，組織 API 會 404，改打 users API
        if repos_resp.status_code == 404:
            repos_resp = requests.get(
                f"https://api.github.com/users/{org}/repos",
                headers=headers,
                params={"sort": "pushed", "per_page": 30},
                timeout=30,
            )
        repos_resp.raise_for_status()
        repos = repos_resp.json()

        for repo in repos:
            repo_name = repo.get("name", "")
            rel_resp = requests.get(
                f"https://api.github.com/repos/{org}/{repo_name}/releases/latest",
                headers=headers,
                timeout=30,
            )
            # 沒有 release 的 repo 會 404，跳過
            if rel_resp.status_code != 200:
                continue
            rel = rel_resp.json()
            tag = rel.get("tag_name", "")
            items.append({
                "source": source["name"],
                "uid": f"{org}/{repo_name}@{tag}",
                "title": f"{repo_name} {tag}：{rel.get('name', '')}".strip(),
                "link": rel.get("html_url", ""),
                "summary": (rel.get("body", "") or "")[:2000],
                "published": rel.get("published_at", ""),
                "fetched_at": _now_iso(),
            })
    except Exception as e:
        logger.warning("抓 GitHub release 失敗 %s：%s", source["name"], e)
    return items


def _fetch_one(source):
    if source["type"] == "rss":
        return _fetch_rss(source)
    if source["type"] == "github_releases":
        return _fetch_github_releases(source)
    logger.warning("未知的來源類型：%s", source.get("type"))
    return []


# ============================================================
# 主流程：掃所有來源
# ============================================================

def scan_all_sources():
    """掃過所有來源，回傳這次「新」抓到的項目 list（沒看過的）。

    順帶做三件事：
    1. 把新項目存進情報庫（全部留著，供問答）
    2. 更新 seen 記錄（避免下次重複推）
    3. 更新每個來源的健康時間戳
    """
    seen = _load_json(SEEN_FILE, {})            # uid -> True
    intel = _load_json(INTEL_FILE, [])          # 全部抓過的項目
    health = _load_json(SOURCE_HEALTH_FILE, {}) # source name -> 上次有新東西的時間

    new_items = []

    for source in SOURCES:
        logger.info("掃描來源：%s", source["name"])
        items = _fetch_one(source)

        got_new_this_source = False
        for item in items:
            uid = item["uid"]
            if not uid or uid in seen:
                continue
            # 新項目
            seen[uid] = True
            intel.append(item)
            new_items.append(item)
            got_new_this_source = True

        # 只要這個來源「成功抓到任何東西」（不管新舊），就更新健康時間
        # 因為「抓得到內容」就代表來源是活的；完全抓不到才算可疑
        if items:
            health[source["name"]] = _now_iso()

    # 存檔
    _save_json(SEEN_FILE, seen)
    _save_json(INTEL_FILE, intel)
    _save_json(SOURCE_HEALTH_FILE, health)

    logger.info("本次掃描完成，新項目 %d 則", len(new_items))
    return new_items


# ============================================================
# 問答時用：讀出整個情報庫
# ============================================================

def load_intel():
    """讀出抓過的所有情報（含沒推播的），給問答模組查詢用。"""
    return _load_json(INTEL_FILE, [])


# ============================================================
# 健康監控：找出超過 N 天沒更新的來源
# ============================================================

def check_stale_sources():
    """回傳超過 SOURCE_STALE_DAYS 天沒有任何新東西的來源 list。

    回傳格式：[{"name": ..., "days_silent": ..., "note": ...}, ...]
    給主程式拿去組提醒訊息。
    """
    health = _load_json(SOURCE_HEALTH_FILE, {})
    now = datetime.now(timezone.utc)
    stale = []

    for source in SOURCES:
        name = source["name"]
        last_iso = health.get(name)
        if not last_iso:
            # 從來沒成功抓到過——可能一開始網址就錯了，也值得提醒
            stale.append({
                "name": name,
                "days_silent": None,  # None 代表「從未成功」
                "note": source.get("note", ""),
            })
            continue
        try:
            last = datetime.fromisoformat(last_iso)
        except ValueError:
            continue
        days = (now - last).days
        if days >= SOURCE_STALE_DAYS:
            stale.append({
                "name": name,
                "days_silent": days,
                "note": source.get("note", ""),
            })

    return stale
