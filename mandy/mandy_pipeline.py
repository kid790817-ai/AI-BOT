import asyncio
from dataclasses import dataclass, field
from typing import Optional

from mandy_config import (
    CLAUDE_MAIN_MODEL,
    CLAUDE_REVIEW_MODEL,
    USE_GROK_SECOND_OPINION,
    OUTPUT_PREFIXES,
)
from mandy_clients import call_perplexity, call_claude, call_grok
from mandy_prompts import (
    PHASE1_PREWATCH,
    PHASE1_REVIEW,
    PHASE2_PREWATCH,
    PHASE2_REVIEW,
    PHASE3_PREWATCH,
    PHASE3_REVIEW,
    PHASE4_PREWATCH,
    PHASE4_REVIEW,
    GROK_SECOND_OPINION,
    PHASE5_FINALIZE_PREWATCH,
    PHASE5_FINALIZE_REVIEW,
    SEO_PACK_PROMPT,
)
from mandy_utils import safe_filename, send_txt, mode_label, MandyError


@dataclass
class MandyJob:
    mode: str
    title: str
    channel_id: int
    status: str = "準備中"
    research: Optional[str] = None
    angles: Optional[str] = None
    structure: Optional[str] = None
    draft: Optional[str] = None
    second_opinion: str = "未使用 Grok 第二意見。"
    final_article: Optional[str] = None
    seo_pack: Optional[str] = None
    outputs: list[str] = field(default_factory=list)


async def _run_blocking(func, *args, **kwargs):
    """
    Discord bot 是 async。
    即使單頻道使用，也用 to_thread 避免長 API 請求卡住 heartbeat。
    """
    return await asyncio.to_thread(func, *args, **kwargs)


async def _send_step_file(channel, job: MandyJob, key: str, content: str):
    prefix = OUTPUT_PREFIXES[key]
    title = safe_filename(job.title)
    filename = f"{prefix}_{mode_label(job.mode)}_{title}.txt"
    await send_txt(channel, filename, content)
    job.outputs.append(filename)


async def run_mandy_pipeline(channel, job: MandyJob) -> MandyJob:
    label = mode_label(job.mode)
    await channel.send(f"收到：{label}｜{job.title}\n開始產生，流程會自動跑完。")

    # Phase 1
    job.status = "Phase 1：搜尋與整理原始資料"
    await channel.send(job.status)
    phase1_prompt = PHASE1_REVIEW if job.mode == "review" else PHASE1_PREWATCH
    job.research = await _run_blocking(call_perplexity, phase1_prompt.format(title=job.title))
    await _send_step_file(channel, job, "research", job.research)

    # Phase 2
    job.status = "Phase 2：挑選文章角度"
    await channel.send(job.status)
    phase2_prompt = PHASE2_REVIEW if job.mode == "review" else PHASE2_PREWATCH
    job.angles = await _run_blocking(
        call_claude,
        phase2_prompt.format(research=job.research),
        CLAUDE_MAIN_MODEL,
    )
    await _send_step_file(channel, job, "angle_plan", job.angles)

    # Phase 3
    job.status = "Phase 3：建立文章架構"
    await channel.send(job.status)
    phase3_prompt = PHASE3_REVIEW if job.mode == "review" else PHASE3_PREWATCH
    job.structure = await _run_blocking(
        call_claude,
        phase3_prompt.format(title=job.title, angles=job.angles),
        CLAUDE_MAIN_MODEL,
    )
    await _send_step_file(channel, job, "structure", job.structure)

    # Phase 4
    job.status = "Phase 4：撰寫初稿"
    await channel.send(job.status)
    phase4_prompt = PHASE4_REVIEW if job.mode == "review" else PHASE4_PREWATCH
    job.draft = await _run_blocking(
        call_claude,
        phase4_prompt.format(structure=job.structure, research=job.research),
        CLAUDE_MAIN_MODEL,
    )

    # Optional Grok second opinion
    if USE_GROK_SECOND_OPINION:
        job.status = "Phase 5：取得第二意見"
        await channel.send(job.status)
        try:
            job.second_opinion = await _run_blocking(
                call_grok,
                GROK_SECOND_OPINION.format(article=job.draft),
            )
        except Exception as e:
            job.second_opinion = f"Grok 第二意見略過：{e}"

    # Phase 5 finalize
    job.status = "Phase 6：最終修稿與檢查"
    await channel.send(job.status)
    finalize_prompt = PHASE5_FINALIZE_REVIEW if job.mode == "review" else PHASE5_FINALIZE_PREWATCH
    job.final_article = await _run_blocking(
        call_claude,
        finalize_prompt.format(
            draft=job.draft,
            research=job.research,
            second_opinion=job.second_opinion,
        ),
        CLAUDE_REVIEW_MODEL,
    )
    await _send_step_file(channel, job, "final_article", job.final_article)

    # SEO Pack
    job.status = "Phase 7：產出 SEO 輔助資料"
    await channel.send(job.status)
    job.seo_pack = await _run_blocking(
        call_claude,
        SEO_PACK_PROMPT.format(article=job.final_article, research=job.research),
        CLAUDE_REVIEW_MODEL,
    )
    await _send_step_file(channel, job, "seo_pack", job.seo_pack)

    job.status = "完成"
    await channel.send(
        "完成。\n"
        "已輸出：\n"
        "1. 研究資料\n"
        "2. 文章角度\n"
        "3. 文章架構\n"
        "4. 最終文章\n"
        "5. SEO 輔助資料\n\n"
        "最重要的是 04_final_article 和 05_seo_pack。"
    )
    return job
