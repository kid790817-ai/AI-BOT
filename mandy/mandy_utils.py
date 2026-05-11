import os
import re
import tempfile
from dataclasses import dataclass
from typing import Optional

import discord


class MandyError(Exception):
    """Mandy 可讀錯誤。丟給 Discord 使用者看。"""


@dataclass
class ParsedCommand:
    mode: str       # prewatch / review
    title: str
    raw: str


def parse_mandy_command(content: str) -> Optional[ParsedCommand]:
    """
    只接受：
    觀影前 片名
    影評 片名

    不接受其他閒聊，避免誤啟動。
    """
    text = content.strip()

    for prefix, mode in [("觀影前", "prewatch"), ("影評", "review")]:
        if text == prefix:
            raise MandyError(f"請輸入片名，例如：{prefix} 沙丘2")

        if text.startswith(prefix + " "):
            title = text[len(prefix):].strip()
            if not title:
                raise MandyError(f"請輸入片名，例如：{prefix} 沙丘2")
            return ParsedCommand(mode=mode, title=title, raw=text)

    return None


def mode_label(mode: str) -> str:
    return "觀影前" if mode == "prewatch" else "影評"


def safe_filename(text: str, max_len: int = 60) -> str:
    """
    清理 Discord 檔名，避免片名含 / : ? 等字元造成問題。
    """
    text = text.strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._ ")
    if not text:
        text = "untitled"
    return text[:max_len]


async def send_txt(channel, filename: str, content: str):
    """
    把文字內容暫存成 txt 後傳到 Discord。
    """
    if not isinstance(content, str):
        content = str(content)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name

    try:
        await channel.send(file=discord.File(tmp_path, filename=filename))
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


def section(title: str, body: str) -> str:
    return f"【{title}】\n{body.strip()}\n"


def compact_error(e: Exception) -> str:
    msg = str(e).strip()
    if not msg:
        msg = e.__class__.__name__
    if len(msg) > 1500:
        msg = msg[:1500] + "..."
    return msg
