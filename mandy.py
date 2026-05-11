import asyncio
import discord
from discord.ext import commands

from mandy_config import DISCORD_TOKEN
from mandy_pipeline import MandyJob, run_mandy_pipeline
from mandy_utils import parse_mandy_command, mode_label, MandyError, compact_error


# ─────────────────────────────────────────
# Discord 初始化
# ─────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

active_job: MandyJob | None = None
active_task: asyncio.Task | None = None
last_command: tuple[str, str] | None = None


@bot.event
async def on_ready():
    print(f"Mandy 上線：{bot.user}")


@bot.event
async def on_message(message):
    global active_job, active_task, last_command

    if message.author.bot:
        return

    content = message.content.strip()

    # ─────────────────────────────────────
    # 保命指令
    # ─────────────────────────────────────

    if content == "狀態":
        if active_job and active_task and not active_task.done():
            await message.channel.send(
                f"目前任務：{mode_label(active_job.mode)}｜{active_job.title}\n"
                f"進度：{active_job.status}"
            )
        else:
            await message.channel.send("目前沒有進行中的任務。")
        return

    if content == "取消":
        if active_task and not active_task.done():
            active_task.cancel()
            await message.channel.send("已送出取消。若 API 正在回應中，可能會在該段結束後停止。")
        else:
            await message.channel.send("目前沒有可以取消的任務。")
        active_job = None
        active_task = None
        return

    if content == "重跑":
        if not last_command:
            await message.channel.send("沒有上一個任務可以重跑。")
            return

        if active_task and not active_task.done():
            await message.channel.send("目前已有任務進行中，請先輸入「取消」或等它完成。")
            return

        mode, title = last_command
        active_job = MandyJob(mode=mode, title=title, channel_id=message.channel.id)
        active_task = asyncio.create_task(_run_job(message.channel, active_job))
        return

    # ─────────────────────────────────────
    # 主指令：觀影前 片名 / 影評 片名
    # ─────────────────────────────────────

    try:
        parsed = parse_mandy_command(content)
    except MandyError as e:
        await message.channel.send(str(e))
        return

    if parsed is None:
        await bot.process_commands(message)
        return

    if active_task and not active_task.done():
        await message.channel.send(
            "目前已有任務進行中。\n"
            "輸入「狀態」查看進度，或輸入「取消」中止目前任務。"
        )
        return

    active_job = MandyJob(
        mode=parsed.mode,
        title=parsed.title,
        channel_id=message.channel.id,
    )
    last_command = (parsed.mode, parsed.title)
    active_task = asyncio.create_task(_run_job(message.channel, active_job))


async def _run_job(channel, job: MandyJob):
    global active_job, active_task

    try:
        await run_mandy_pipeline(channel, job)

    except asyncio.CancelledError:
        await channel.send("任務已取消。")

    except Exception as e:
        await channel.send(
            "任務失敗。\n"
            f"失敗階段：{job.status}\n"
            f"錯誤：{compact_error(e)}"
        )

    finally:
        active_job = None
        active_task = None


bot.run(DISCORD_TOKEN)
