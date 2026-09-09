import os
import sys
import asyncio
from pathlib import Path
import discord
from discord import app_commands
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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# 자동 발행 알림을 보낼 디스코드 채널 ID 저장
TARGET_CHANNEL_ID = None
AUTO_INTERVAL_MINUTES = 60 # 기본 60분 간격

from instagram_uploader import upload_reels_to_instagram

LAST_PROCESSED_VIDEO = {}  # channel_id: {'url': ..., 'id': ..., 'line1': ..., 'line2': ..., 'sub': ...}

class EditModal(discord.ui.Modal, title="🎬 릴스 타이틀 및 텍스트 수정"):
    line1_input = discord.ui.TextInput(
        label="상단 1줄 (핑크색 하이라이트)",
        placeholder="예: 역대급 웃긴 고양이",
        default="역대급 웃긴 고양이",
        max_length=30
    )
    line2_input = discord.ui.TextInput(
        label="상단 2줄 (굵은 흰색 메인 타이틀)",
        placeholder="예: 모먼트 랭킹 TOP5",
        default="모먼트 랭킹 TOP5",
        max_length=30
    )
    sub_input = discord.ui.TextInput(
        label="상단 3줄 (괄호 반응 유도 문구)",
        placeholder="예: (다들 몇 번이 제일 웃김? ㅋㅋㅋ)",
        default="(다들 몇 번이 제일 웃김? ㅋㅋㅋ)",
        max_length=40,
        required=False
    )

    def __init__(self, video_url: str, video_id: str, channel: discord.TextChannel, orig_line1="", orig_line2="", orig_sub=""):
        super().__init__()
        self.video_url = video_url
        self.video_id = video_id
        self.channel = channel
        if orig_line1:
            self.line1_input.default = orig_line1
        if orig_line2:
            self.line2_input.default = orig_line2
        if orig_sub:
            self.sub_input.default = orig_sub

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        status_msg = await self.channel.send(
            f"🛠️ **[재제작 중]** 입력하신 타이틀로 릴스를 다시 편집하고 있습니다...\n"
            f"- 1줄: `{self.line1_input.value}`\n"
            f"- 2줄: `{self.line2_input.value}`\n"
            f"- 서브: `{self.sub_input.value}`"
        )
        try:
            loop = asyncio.get_event_loop()
            reels_path = await loop.run_in_executor(
                None,
                lambda: create_reels_pipeline(
                    video_url=self.video_url,
                    line1_text=self.line1_input.value,
                    line2_text=self.line2_input.value,
                    sub_text=self.sub_input.value
                )
            )
            filename = Path(reels_path).name
            view = ReelsApprovalView(
                reels_filename=filename,
                video_id=self.video_id,
                video_url=self.video_url,
                channel=self.channel,
                line1=self.line1_input.value,
                line2=self.line2_input.value,
                sub=self.sub_input.value
            )
            discord_file = discord.File(reels_path, filename=filename)
            await self.channel.send(
                content=f"✨ **수정된 릴스가 완성되었습니다!**\n🔗 원본 링크: {self.video_url}\n수정된 영상을 확인해 주세요:",
                file=discord_file,
                view=view
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(content=f"⚠️ 영상 수정 제작 중 오류 발생: `{str(e)}`")

class ReelsApprovalView(discord.ui.View):
    def __init__(self, reels_filename: str, video_id: str, video_url: str, channel: discord.TextChannel, line1="", line2="", sub=""):
        super().__init__(timeout=None)
        self.reels_filename = reels_filename
        self.video_id = video_id
        self.video_url = video_url
        self.channel = channel
        self.line1 = line1
        self.line2 = line2
        self.sub = sub

    @discord.ui.button(label="✅ 인스타 업로드 승인", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True
        save_processed_id(self.video_id)
        
        await interaction.message.edit(
            content=f"🚀 **[승인 완료]** 인스타그램 계정으로 릴스 업로드를 진행하고 있습니다...\n잠시만 기다려 주세요! (약 15초 소요)",
            view=self
        )

        reels_path = str(OUTPUT_DIR / self.reels_filename)
        try:
            loop = asyncio.get_event_loop()
            title_text = f"{self.line1} {self.line2}".strip() or "역대급 해외 바이럴 영상"
            res = await loop.run_in_executor(
                None,
                lambda: upload_reels_to_instagram(reels_path, title=title_text)
            )
            await self.channel.send(
                f"🎉 **인스타그램 릴스 업로드 성공!**\n"
                f"지금 바로 인스타에서 확인해 보세요:\n"
                f"👉 **{res['url']}**"
            )
        except Exception as e:
            await self.channel.send(f"⚠️ 인스타그램 업로드 중 오류 발생: `{str(e)}`\n(인스타그램 설정을 확인해 주세요)")

    @discord.ui.button(label="✏️ 자막/제목 직접 수정", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EditModal(
            video_url=self.video_url,
            video_id=self.video_id,
            channel=self.channel,
            orig_line1=self.line1,
            orig_line2=self.line2,
            orig_sub=self.sub
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❌ 반려 / 다른 영상 찾기", style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True
        save_processed_id(self.video_id)
        await interaction.message.edit(
            content=f"🗑️ **[반려 완료]** `{self.reels_filename}` 영상이 반려되었습니다. 다음 영상을 탐색합니다!",
            view=self
        )
        await process_auto_reels(self.channel)


async def process_auto_reels(channel: discord.TextChannel, interaction: discord.Interaction = None):
    """
    해외 바이럴 영상을 자동으로 찾아 릴스로 편집 후 디스코드 채널로 전송
    (비공개/오류 영상은 내부적으로 자동 건너뛰고 오직 100% 검증된 성공 영상만 단 1개 전송)
    """
    init_text = "🔍 **실시간 해외 바이럴 인기 영상을 탐색하고 있습니다...**"
    status_msg = None

    async def update_status(text: str):
        try:
            if interaction:
                await interaction.edit_original_response(content=text)
            elif status_msg:
                await status_msg.edit(content=text)
        except Exception:
            pass

    if interaction:
        # 슬래시 커맨드 인터랙션: 이미 defer 완료되었으므로 original_response를 수정하여 단 1개의 메시지만 유지
        await interaction.edit_original_response(content=init_text)
    else:
        status_msg = await channel.send(init_text)

    loop = asyncio.get_event_loop()

    for attempt in range(5):
        found = None
        try:
            found = await loop.run_in_executor(None, find_viral_video)

            await update_status(
                f"⚙️ **[영상 발견]** `{found['line1']} {found['line2']}`\n인스타그램 릴스 최적화 및 상황별 효과음 믹싱 중... (약 15초)"
            )

            reels_path = await loop.run_in_executor(
                None,
                lambda: create_reels_pipeline(
                    video_url=found['url'],
                    line1_text=found.get('line1', '해외에서 화제 된'),
                    line2_text=found.get('line2', '눈길을 사로잡는 순간'),
                    sub_text=found.get('sub', '(끝까지 보게 되는 장면)')
                )
            )

            filename = Path(reels_path).name
            file_size_mb = os.path.getsize(reels_path) / (1024 * 1024)

            if file_size_mb > 10:
                print(f"영상 용량({file_size_mb:.1f}MB)이 디스코드 제한(10MB)을 초과하여 다음 영상으로 자동 전환합니다.")
                save_processed_id(found['id'])
                continue

            LAST_PROCESSED_VIDEO[channel.id] = {
                'url': found['url'],
                'id': found['id'],
                'line1': found.get('line1', '해외에서 화제 된'),
                'line2': found.get('line2', '눈길을 사로잡는 순간'),
                'sub': found.get('sub', '(끝까지 보게 되는 장면)'),
                'filename': filename
            }

            view = ReelsApprovalView(
                reels_filename=filename,
                video_id=found['id'],
                video_url=found['url'],
                channel=channel,
                line1=found.get('line1', '해외에서 화제 된'),
                line2=found.get('line2', '눈길을 사로잡는 순간'),
                sub=found.get('sub', '(끝까지 보게 되는 장면)')
            )
            discord_file = discord.File(reels_path, filename=filename)

            complete_content = (
                f"🔔 **새로운 릴스가 완성되었습니다!**\n"
                f"🔗 원본 링크: {found['url']}\n"
                f"영상을 확인하시고 업로드 여부를 결정해 주세요 (수정이 필요하면 **[✏️ 자막/제목 직접 수정]** 버튼 클릭!):"
            )

            if interaction:
                # 단 1개의 디스코드 메시지에서 완성 영상 + 승인/수정/반려 버튼으로 완성! (중복 메시지 0개)
                await interaction.edit_original_response(
                    content=complete_content,
                    attachments=[discord_file],
                    view=view
                )
            else:
                await channel.send(
                    content=complete_content,
                    file=discord_file,
                    view=view
                )
                try:
                    if status_msg:
                        await status_msg.delete()
                except Exception:
                    pass

            return # 성공 시 단 1개의 완성 영상만 남기고 종료!

        except Exception as e:
            err_text = str(e)
            if found and 'id' in found:
                save_processed_id(found['id'])
            print(f"[자동 스킵] 영상 처리 예외 ({err_text[:80]}), 다음 영상 조용히 자동 탐색...")
            # 채팅창에 지저분한 시도 3/5 에러를 도배하지 않고 차분한 탐색 상태 유지
            await update_status("🔍 **최적의 바이럴 영상을 분석하여 릴스로 제작하고 있습니다... ⏳**")
            await asyncio.sleep(1)

    fail_msg = "⚠️ 인기 영상을 다운로드하는 중 일시적인 오류가 발생했습니다. 잠시 후 `/탐색`을 다시 시도해 주세요."
    await update_status(fail_msg)

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
    print("==========================================", flush=True)
    print(f"🤖 릴스 전자동 매니저 봇 온라인! ({bot.user.name})", flush=True)
    try:
        # 중복 표시 방지: 길드별 로컬 커맨드 중복 제거 (Clear)
        for guild in bot.guilds:
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
        
        # 글로벌 슬래시 커맨드 1벌만 깔끔하게 동기화
        synced = await bot.tree.sync()
        print(f"✓ 디스코드 슬래시 커맨드 {len(synced)}개 단일 등록 동기화 완료!", flush=True)
    except Exception as e:
        print(f"슬래시 커맨드 동기화 안내: {e}", flush=True)
    print("디스코드 슬래시 명령어: /탐색, /수정, /자동켜기, /자동끄기, /무인on, /무인off, /명령어", flush=True)
    print("==========================================", flush=True)




# ==========================================
# 🚀 슬래시 커맨드 (Slash Commands: /명령어)
# ==========================================

@bot.tree.command(name="탐색", description="지금 즉시 인기 랭킹 쇼츠/해외 바이럴 영상을 찾아 릴스로 제작합니다.")
async def slash_find(interaction: discord.Interaction):
    global TARGET_CHANNEL_ID
    TARGET_CHANNEL_ID = interaction.channel.id
    await interaction.response.defer()
    await process_auto_reels(interaction.channel, interaction=interaction)


@bot.tree.command(name="수정", description="특정 영상 또는 최근 영상을 원하는 제목과 문구로 다시 제작합니다.")
@app_commands.describe(
    제목="원하는 제목 (예: 모먼트 랭킹 TOP5 또는 1줄 / 2줄 / 서브문구)",
    유튜브링크="수정할 유튜브 영상 링크 (비워두면 가장 최근 생성된 영상을 재편집합니다)"
)
async def slash_edit(interaction: discord.Interaction, 제목: str, 유튜브링크: str = ""):
    await interaction.response.defer()
    channel_id = interaction.channel.id
    target_url = 유튜브링크.strip()
    line1 = "역대급 해외 바이럴"
    line2 = "모먼트 랭킹 TOP5"
    sub = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)"

    if not target_url:
        last_info = LAST_PROCESSED_VIDEO.get(channel_id)
        if last_info:
            target_url = last_info['url']
            line1 = last_info.get('line1', line1)
            line2 = last_info.get('line2', line2)
            sub = last_info.get('sub', sub)
        else:
            await interaction.edit_original_response(
                content="⚠️ 최근 작업한 영상이 없습니다. `유튜브링크` 옵션에 영상 URL을 함께 입력해 주세요!"
            )
            return

    parts = [p.strip() for p in 제목.split("/") if p.strip()]
    if len(parts) >= 3:
        line1, line2, sub = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        line1, line2 = parts[0], parts[1]
    elif len(parts) == 1:
        line2 = parts[0]

    await interaction.edit_original_response(
        content=(
            f"🛠️ **[릴스 재제작 시작]** 영상을 요청하신 설정으로 다시 편집하고 있습니다...\n"
            f"- 대상 영상: {target_url}\n"
            f"- 1줄 타이틀: `{line1}`\n"
            f"- 2줄 타이틀: `{line2}`\n"
            f"- 서브 훅: `{sub}`\n"
            f"⏳ 약 15초 소요됩니다."
        )
    )

    try:
        loop = asyncio.get_event_loop()
        reels_path = await loop.run_in_executor(
            None,
            lambda: create_reels_pipeline(
                video_url=target_url,
                line1_text=line1,
                line2_text=line2,
                sub_text=sub
            )
        )
        filename = Path(reels_path).name
        video_id = Path(target_url).name

        LAST_PROCESSED_VIDEO[channel_id] = {
            'url': target_url,
            'id': video_id,
            'line1': line1,
            'line2': line2,
            'sub': sub,
            'filename': filename
        }

        view = ReelsApprovalView(
            reels_filename=filename,
            video_id=video_id,
            video_url=target_url,
            channel=interaction.channel,
            line1=line1,
            line2=line2,
            sub=sub
        )
        discord_file = discord.File(reels_path, filename=filename)

        await interaction.edit_original_response(
            content=f"✨ **수정된 릴스가 완성되었습니다!**\n🔗 원본 링크: {target_url}\n마음에 드시면 **[✅ 인스타 업로드 승인]**을 눌러주세요:",
            attachments=[discord_file],
            view=view
        )
    except Exception as e:
        await interaction.edit_original_response(content=f"⚠️ 영상 재제작 중 오류 발생: `{str(e)}`")

@bot.tree.command(name="자동켜기", description="지정한 시간(분)마다 자동으로 영상을 찾아 릴스로 편집 후 배달합니다.")
@app_commands.describe(간격_분="탐색 주기(분 단위, 기본: 60분)")
async def slash_start_auto(interaction: discord.Interaction, 간격_분: int = 60):
    global TARGET_CHANNEL_ID, AUTO_INTERVAL_MINUTES
    TARGET_CHANNEL_ID = interaction.channel.id
    AUTO_INTERVAL_MINUTES = 간격_분
    
    auto_schedule_task.change_interval(minutes=간격_분)
    if not auto_schedule_task.is_running():
        auto_schedule_task.start()
    
    await interaction.response.send_message(
        f"🚀 **무인 자동화 가동!** 이제 **{간격_분}분**마다 해외 바이럴 영상을 알아서 찾아 릴스로 편집 후 이곳에 배달합니다!"
    )

@bot.tree.command(name="자동끄기", description="정기 자동 릴스 탐색 및 배달을 중지합니다.")
async def slash_stop_auto(interaction: discord.Interaction):
    if auto_schedule_task.is_running():
        auto_schedule_task.stop()
    await interaction.response.send_message("🛑 정기 자동 탐색이 중지되었습니다.")

@bot.tree.command(name="무인on", description="승인 요청 없이 2시간마다 인스타로 바로 즉시 발행하는 완전 무인 모드를 켭니다.")
async def slash_direct_on(interaction: discord.Interaction):
    global TARGET_CHANNEL_ID, AUTO_DIRECT_UPLOAD
    TARGET_CHANNEL_ID = interaction.channel.id
    AUTO_DIRECT_UPLOAD = True

    auto_schedule_task.change_interval(minutes=120)
    if not auto_schedule_task.is_running():
        auto_schedule_task.start()

    await interaction.response.send_message(
        "🔥 **[완전 무인 모드 ON]**\n"
        "이제 **승인 요청 없이 2시간마다** 알아서 영상을 찾아 릴스로 만들고 **인스타그램에 바로바로 업로드**합니다!\n"
        "(취소하고 싶으시면 `/무인off`를 입력하세요)"
    )

@bot.tree.command(name="무인off", description="완전 무인 모드를 끄고 영상 확인 후 승인하는 검수 모드로 복귀합니다.")
async def slash_direct_off(interaction: discord.Interaction):
    global AUTO_DIRECT_UPLOAD
    AUTO_DIRECT_UPLOAD = False
    await interaction.response.send_message("🛡️ **[승인 검수 모드로 전환]** 이제 영상이 만들어지면 승인 버튼을 먼저 보냅니다.")

@bot.tree.command(name="명령어", description="릴스 자동화 봇의 모든 사용 가능한 명령어 안내를 확인합니다.")
async def slash_help(interaction: discord.Interaction):
    help_text = (
        "📖 **릴스 자동화 봇 슬래시(/) 명령어 안내**\n\n"
        "채팅창에 `/`만 치셔도 아래의 모든 명령어가 자동완성 팝업으로 뜹니다!\n\n"
        "🔍 **탐색 및 제작**\n"
        "• `/탐색` : 지금 즉시 인기 랭킹 쇼츠/바이럴 영상을 찾아 릴스 제작\n"
        "• `https://유튜브링크` : 링크만 채팅에 붙여넣어도 해당 영상으로 즉시 릴스 제작\n\n"
        "✏️ **영상 수정 및 재제작**\n"
        "• **버튼 클릭**: 영상 아래 **[✏️ 자막/제목 직접 수정]** 버튼을 누르면 팝업창에서 바로 수정 가능!\n"
        "• `/수정 <제목> [유튜브링크]` : 특정 영상 또는 최근 영상을 원하는 제목으로 다시 제작\n\n"
        "⏰ **자동 스케줄러 & 무인 모드**\n"
        "• `/자동켜기 [간격_분]` : 지정한 분마다 자동으로 영상을 찾아 배달 (기본 60분)\n"
        "• `/자동끄기` : 자동 배달 중지\n"
        "• `/무인on` : 승인 버튼 없이 2시간마다 인스타로 바로 즉시 발행하는 완전 무인 모드\n"
        "• `/무인off` : 승인 검수 모드로 복귀\n"
        "• `/명령어` : 전체 명령어 및 도움말 보기\n"
    )
    await interaction.response.send_message(help_text)


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

@bot.command(name="수정", aliases=["재제작", "편집"])

async def cmd_edit(ctx, *, args: str = ""):
    """
    영상을 원하는 제목과 텍스트로 수정하여 다시 제작합니다.
    사용법:
      1) !수정 <유튜브링크> [1줄] / [2줄] / [서브문구]
      2) !수정 [새로운 제목]  (가장 최근 영상에 새 제목 적용)
    """
    args = args.strip()
    channel_id = ctx.channel.id
    target_url = None
    line1 = "역대급 해외 바이럴"
    line2 = "모먼트 랭킹 TOP5"
    sub = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)"

    # 1. 링크가 포함되어 있는지 확인
    words = args.split()
    if words and (words[0].startswith("http://") or words[0].startswith("https://")):
        target_url = words[0]
        remaining_text = " ".join(words[1:])
    else:
        # 최근 영상 기록 확인
        last_info = LAST_PROCESSED_VIDEO.get(channel_id)
        if last_info:
            target_url = last_info['url']
            line1 = last_info.get('line1', line1)
            line2 = last_info.get('line2', line2)
            sub = last_info.get('sub', sub)
            remaining_text = args
        else:
            await ctx.reply(
                "⚠️ 수정할 영상을 찾을 수 없습니다.\n"
                "사용법: `!수정 <유튜브URL> [1줄제목] / [2줄제목]` 형태로 입력하시거나,\n"
                "완성된 영상 아래의 **[✏️ 자막/제목 직접 수정]** 버튼을 눌러주세요!"
            )
            return

    # 2. 텍스트 분리 처리 (구분자 '/' 지원)
    if remaining_text:
        parts = [p.strip() for p in remaining_text.split("/") if p.strip()]
        if len(parts) >= 3:
            line1, line2, sub = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            line1, line2 = parts[0], parts[1]
        elif len(parts) == 1:
            line2 = parts[0]

    status_msg = await ctx.reply(
        f"🛠️ **[릴스 재제작 시작]** 영상을 요청하신 설정으로 다시 편집하고 있습니다...\n"
        f"- 대상 영상: {target_url}\n"
        f"- 1줄 타이틀: `{line1}`\n"
        f"- 2줄 타이틀: `{line2}`\n"
        f"- 서브 훅: `{sub}`\n"
        f"⏳ 약 15초 소요됩니다."
    )

    try:
        loop = asyncio.get_event_loop()
        reels_path = await loop.run_in_executor(
            None,
            lambda: create_reels_pipeline(
                video_url=target_url,
                line1_text=line1,
                line2_text=line2,
                sub_text=sub
            )
        )
        filename = Path(reels_path).name
        video_id = Path(target_url).name

        LAST_PROCESSED_VIDEO[channel_id] = {
            'url': target_url,
            'id': video_id,
            'line1': line1,
            'line2': line2,
            'sub': sub,
            'filename': filename
        }

        view = ReelsApprovalView(
            reels_filename=filename,
            video_id=video_id,
            video_url=target_url,
            channel=ctx.channel,
            line1=line1,
            line2=line2,
            sub=sub
        )
        discord_file = discord.File(reels_path, filename=filename)

        await ctx.reply(
            content=f"✨ **수정된 릴스가 완성되었습니다!**\n🔗 원본 링크: {target_url}\n마음에 드시면 **[✅ 인스타 업로드 승인]**을 눌러주세요:",
            file=discord_file,
            view=view
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(content=f"⚠️ 영상 재제작 중 오류 발생: `{str(e)}`")

@bot.command(name="명령어", aliases=["도움말", "help"])
async def cmd_help(ctx):
    """사용 가능한 명령어 안내"""
    help_text = (
        "📖 **릴스 자동화 봇 사용 가능한 명령어 안내**\n\n"
        "🔍 **탐색 및 제작**\n"
        "• `!탐색` 또는 `!자동` : 지금 즉시 인기 랭킹 쇼츠/바이럴 영상을 찾아 릴스 제작\n"
        "• `https://유튜브링크` : 링크만 채팅에 붙여넣으면 해당 영상으로 즉시 릴스 제작\n\n"
        "✏️ **영상 수정 및 재제작**\n"
        "• **버튼 클릭**: 영상 아래 **[✏️ 자막/제목 직접 수정]** 버튼을 누르면 팝업창에서 바로 수정 가능!\n"
        "• `!수정 [새제목]` : 직전에 만든 영상의 제목을 바꿔서 다시 제작\n"
        "• `!수정 <유튜브링크> 1줄 / 2줄 / 서브` : 특정 영상을 원하는 텍스트로 지정 제작\n\n"
        "⏰ **자동 스케줄러 & 무인 모드**\n"
        "• `!자동켜기 <분>` : N분마다 자동으로 영상을 찾아 디스코드로 배달 (기본 60분)\n"
        "• `!자동끄기` : 자동 배달 중지\n"
        "• `!무인on` : 승인 버튼 없이 2시간마다 인스타로 바로 즉시 발행하는 완전 무인 모드\n"
        "• `!무인off` : 승인 검수 모드로 복귀\n"
    )
    await ctx.reply(help_text)

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
            video_id = Path(content).name
            LAST_PROCESSED_VIDEO[message.channel.id] = {
                'url': content,
                'id': video_id,
                'line1': "해외에서 화제 된",
                'line2': "눈길을 사로잡는 순간",
                'sub': "(끝까지 보게 되는 장면)",
                'filename': filename
            }

            view = ReelsApprovalView(
                reels_filename=filename,
                video_id=video_id,
                video_url=content,
                channel=message.channel,
                line1="해외에서 화제 된",
                line2="눈길을 사로잡는 순간",
                sub="(끝까지 보게 되는 장면)"
            )
            discord_file = discord.File(reels_path, filename=filename)

            await message.reply(
                content="✨ **9:16 릴스 제작이 완료되었습니다!** (수정하시려면 **[✏️ 자막/제목 직접 수정]** 버튼 클릭):",
                file=discord_file,
                view=view
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(content=f"⚠️ 오류 발생: `{str(e)}`")


if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
