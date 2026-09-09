import os
import sys
import asyncio
from pathlib import Path
import discord
from discord.ext import commands, tasks
from config import BASE_DIR, OUTPUT_DIR
from pipeline import create_reels_pipeline
from video_finder import find_viral_video, save_processed_id

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
if not DISCORD_BOT_TOKEN and os.path.exists(BASE_DIR / "discord_token.txt"):
    DISCORD_BOT_TOKEN = (BASE_DIR / "discord_token.txt").read_text().strip()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 자동 발행 알림을 보낼 디스코드 채널 ID 저장
TARGET_CHANNEL_ID = None
AUTO_INTERVAL_MINUTES = 60 # 기본 60분 간격

from instagram_uploader import upload_reels_to_instagram

class ReelsApprovalView(discord.ui.View):
    def __init__(self, reels_filename: str, video_id: str, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.reels_filename = reels_filename
        self.video_id = video_id
        self.channel = channel

    @discord.ui.button(label="✅ 인스타 업로드 승인", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        save_processed_id(self.video_id)
        
        await interaction.response.edit_message(
            content=f"🚀 **[승인 완료]** 인스타그램 계정으로 릴스 업로드를 진행하고 있습니다...\n잠시만 기다려 주세요! (약 15초 소요)",
            view=self
        )

        # 인스타그램 업로드 실행
        reels_path = str(OUTPUT_DIR / self.reels_filename)
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None,
                lambda: upload_reels_to_instagram(reels_path)
            )
            await self.channel.send(
                f"🎉 **인스타그램 릴스 업로드 성공!**\n"
                f"지금 바로 인스타에서 확인해 보세요:\n"
                f"👉 **{res['url']}**"
            )
        except Exception as e:
            await self.channel.send(f"⚠️ 인스타그램 업로드 중 오류 발생: `{str(e)}`\n(인스타그램 아이디/비밀번호 설정을 확인해 주세요)")

    @discord.ui.button(label="❌ 반려 / 다른 영상 찾기", style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        save_processed_id(self.video_id)
        await interaction.response.edit_message(
            content=f"🗑️ **[반려 완료]** `{self.reels_filename}` 영상이 반려되었습니다. 다음 영상을 탐색합니다!",
            view=self
        )
        # 반려 시 자동으로 다음 영상 탐색 실행
        await process_auto_reels(self.channel)

async def process_auto_reels(channel: discord.TextChannel):
    """
    해외 바이럴 영상을 자동으로 찾아 릴스로 편집 후 디스코드 채널로 전송
    """
    status_msg = await channel.send("🔍 **실시간 해외 바이럴 인기 영상을 탐색하고 있습니다...**")
    try:
        loop = asyncio.get_event_loop()
        found = await loop.run_in_executor(None, find_viral_video)

        await status_msg.edit(
            content=f"🎯 **바이럴 영상 발견!**\n- 원본: `{found['orig_title']}`\n- 상단 후킹 제목: **{found['top_title']}**\n- 하단 문구: **{found['bottom_text']}**\n\n⚙️ 9:16 릴스로 자동 편집 중입니다... (약 15~20초)"
        )

        reels_path = await loop.run_in_executor(
            None,
            lambda: create_reels_pipeline(
                video_url=found['url'],
                top_title=found['top_title'],
                bottom_text=found['bottom_text']
            )
        )

        filename = Path(reels_path).name
        file_size_mb = os.path.getsize(reels_path) / (1024 * 1024)

        if file_size_mb > 25:
            await status_msg.edit(content=f"⚠️ 영상 크기가 너무 큽니다 ({file_size_mb:.1f}MB). 다른 영상을 탐색해 주세요.")
            return

        view = ReelsApprovalView(reels_filename=filename, video_id=found['id'], channel=channel)
        discord_file = discord.File(reels_path, filename=filename)

        await channel.send(
            content=f"🔔 **새로운 릴스가 완성되었습니다!**\n🔗 원본 링크: {found['url']}\n영상을 확인하시고 업로드 여부를 결정해 주세요:",
            file=discord_file,
            view=view
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(content=f"⚠️ 자동 탐색 및 제작 중 오류 발생: `{str(e)}`")

# 무인 자동 업로드 모드 플래그 (True면 승인 버튼 없이 인스타로 바로 직행)
AUTO_DIRECT_UPLOAD = False

@tasks.loop(minutes=120)
async def auto_schedule_task():
    global TARGET_CHANNEL_ID, AUTO_DIRECT_UPLOAD
    if TARGET_CHANNEL_ID:
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            print("⏰ [정기 스케줄러] 2시간 주기 자동 릴스 실행...")
            if AUTO_DIRECT_UPLOAD:
                # 무인 모드: 승인 없이 바로 릴스 인스타 업로드
                await process_direct_auto_upload(channel)
            else:
                # 승인 모드: 디스코드로 영상 보내고 버튼 대기
                await process_auto_reels(channel)

async def process_direct_auto_upload(channel: discord.TextChannel):
    """승인 없이 인스타로 즉시 발행하는 완전 무인 함수"""
    status_msg = await channel.send("🤖 **[무인 자동화] 2시간 주기 릴스 탐색 및 인스타 즉시 발행 중...**")
    try:
        loop = asyncio.get_event_loop()
        found = await loop.run_in_executor(None, find_viral_video)
        
        reels_path = await loop.run_in_executor(
            None,
            lambda: create_reels_pipeline(
                video_url=found['url'],
                line1_text=found['line1'],
                line2_text=found['line2'],
                sub_text=found['sub'],
                bottom_caption=found['caption']
            )
        )
        save_processed_id(found['id'])

        # 인스타로 즉시 업로드
        res = await loop.run_in_executor(
            None,
            lambda: upload_reels_to_instagram(reels_path)
        )

        filename = Path(reels_path).name
        discord_file = discord.File(reels_path, filename=filename)

        await channel.send(
            content=(
                f"🎉 **[무인 자동 업로드 완료!]** 인스타그램에 새 릴스가 즉시 발행되었습니다!\n"
                f"🔗 **인스타 링크**: {res['url']}\n"
                f"📌 **제목**: {found['line1']} {found['line2']}\n"
                f"💬 **자막**: {found['caption']}"
            ),
            file=discord_file
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(content=f"⚠️ 무인 자동 발행 중 오류: `{str(e)}`")

@bot.command(name="무인on", aliases=["자동업로드on"])
async def cmd_direct_on(ctx):
    """승인 요청 없이 2시간마다 인스타에 바로 올리는 완전 무인 모드 ON"""
    global TARGET_CHANNEL_ID, AUTO_DIRECT_UPLOAD
    TARGET_CHANNEL_ID = ctx.channel.id
    AUTO_DIRECT_UPLOAD = True

    auto_schedule_task.change_interval(minutes=120)
    if not auto_schedule_task.is_running():
        auto_schedule_task.start()

    await ctx.reply(
        "🔥 **[완전 무인 모드 ON]**\n"
        "이제 **승인 요청 없이 2시간마다** 알아서 영상을 찾아 릴스로 만들고 **인스타그램에 바로바로 업로드**합니다!\n"
        "(취소하고 싶으시면 `!무인off`를 입력하세요)"
    )

@bot.command(name="무인off", aliases=["자동업로드off"])
async def cmd_direct_off(ctx):
    """완전 무인 모드 OFF (승인 요청 모드로 복귀)"""
    global AUTO_DIRECT_UPLOAD
    AUTO_DIRECT_UPLOAD = False
    await ctx.reply("🛡️ **[승인 검수 모드로 전환]** 이제 영상이 만들어지면 승인 버튼을 먼저 보냅니다.")

@bot.event
async def on_ready():
    print("==========================================")
    print(f"🤖 릴스 전자동 매니저 봇 온라인! ({bot.user.name})")
    print("디스코드 명령어:")
    print("  !탐색 또는 !자동 : 지금 즉시 해외 바이럴 영상을 찾아 릴스 제작")
    print("  !자동켜기 <분>   : 지정한 분마다 자동으로 영상 찾아서 배달")
    print("  !자동끄기        : 정기 자동 탐색 끄기")
    print("==========================================")

@bot.command(name="탐색", aliases=["자동"])
async def cmd_find(ctx):
    """즉시 해외 바이럴 영상을 찾아서 릴스 제작"""
    global TARGET_CHANNEL_ID
    TARGET_CHANNEL_ID = ctx.channel.id
    await process_auto_reels(ctx.channel)

@bot.command(name="자동켜기")
async def cmd_start_auto(ctx, minutes: int = 60):
    """정기적으로 해외 영상을 찾아 릴스 제작 배달 시작"""
    global TARGET_CHANNEL_ID, AUTO_INTERVAL_MINUTES
    TARGET_CHANNEL_ID = ctx.channel.id
    AUTO_INTERVAL_MINUTES = minutes
    
    auto_schedule_task.change_interval(minutes=minutes)
    if not auto_schedule_task.is_running():
        auto_schedule_task.start()
    
    await ctx.reply(f"🚀 **무인 자동화 가동!** 이제 **{minutes}분**마다 해외 바이럴 영상을 알아서 찾아 릴스로 편집 후 이곳에 배달합니다!")

@bot.command(name="자동끄기")
async def cmd_stop_auto(ctx):
    """정기 자동 배달 중지"""
    if auto_schedule_task.is_running():
        auto_schedule_task.stop()
    await ctx.reply("🛑 정기 자동 탐색이 중지되었습니다.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # 커맨드 우선 처리
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    content = message.content.strip()

    # 링크 직접 입력 시에도 동작
    if content.startswith("http://") or content.startswith("https://"):
        status_msg = await message.reply("🎬 **영상을 다운로드하고 9:16 릴스로 제작 중입니다...**")
        try:
            loop = asyncio.get_event_loop()
            reels_path = await loop.run_in_executor(
                None,
                lambda: create_reels_pipeline(video_url=content)
            )

            filename = Path(reels_path).name
            view = ReelsApprovalView(reels_filename=filename, video_id="custom", channel=message.channel)
            discord_file = discord.File(reels_path, filename=filename)

            await message.reply(
                content="✨ **9:16 릴스 제작이 완료되었습니다!**",
                file=discord_file,
                view=view
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(content=f"⚠️ 오류 발생: `{str(e)}`")

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
