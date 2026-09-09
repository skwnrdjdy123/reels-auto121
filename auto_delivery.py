import os
import sys
import json
import requests
from pathlib import Path
from video_finder import find_viral_video, save_processed_id
from pipeline import create_reels_pipeline

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
if not DISCORD_BOT_TOKEN and os.path.exists(BASE_DIR / "discord_token.txt"):
    DISCORD_BOT_TOKEN = (BASE_DIR / "discord_token.txt").read_text().strip()
DEFAULT_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "1287728913971281923")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

def send_to_discord(video_path: str, found_info: dict, channel_id: str = DEFAULT_CHANNEL_ID, webhook_url: str = DISCORD_WEBHOOK_URL):
    """
    디스코드 채널 또는 웹훅으로 완성된 릴스 mp4 파일과 후킹 문구를 배달합니다.
    """
    caption = (
        f"🎬 **[클라우드 무인 자동 배달] 새로운 릴스가 도착했습니다!**\n\n"
        f"📌 **상단 타이틀**: {found_info['top_title']}\n"
        f"💬 **하단 리액션**: {found_info['bottom_text']}\n"
        f"🔗 **원본 영상 링크**: {found_info['url']}\n"
        f"✨ **원본 제목**: `{found_info['orig_title']}`\n\n"
        f"마음에 드시면 인스타에 업로드해 주세요! 🚀"
    )

    filename = Path(video_path).name

    # 1. 웹훅 URL이 있으면 웹훅으로 전송
    if webhook_url:
        with open(video_path, "rb") as f:
            files = {"file": (filename, f, "video/mp4")}
            res = requests.post(webhook_url, data={"content": caption}, files=files)
            if res.status_code in [200, 204]:
                print("✓ 디스코드 웹훅 전송 성공!")
                return True

    # 2. 봇 토큰과 채널 ID로 직접 API 전송 (가장 확실함)
    if DISCORD_BOT_TOKEN and channel_id:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        with open(video_path, "rb") as f:
            files = {"file": (filename, f, "video/mp4")}
            res = requests.post(url, headers=headers, data={"content": caption}, files=files)
            if res.status_code in [200, 201]:
                print(f"✓ 디스코드 채널({channel_id})로 릴스 배달 성공!")
                return True
            else:
                print(f"⚠️ 디스코드 전송 실패 ({res.status_code}): {res.text}")
                return False

    print("⚠️ 디스코드 전송 설정(토큰 또는 웹훅)이 없습니다.")
    return False

def run_auto_delivery(webhook_url: str = None):
    url = webhook_url or DISCORD_WEBHOOK_URL
    print("==========================================")
    print("🚀 [무인 클라우드] 해외 바이럴 릴스 자동 탐색 및 배달 시작")
    print("==========================================")

    # 1. 인기 바이럴 영상 탐색
    found = find_viral_video()
    print(f"🎯 선택된 영상: {found['orig_title']}")

    # 2. 9:16 릴스 자동 합성
    reels_path = create_reels_pipeline(
        video_url=found['url'],
        line1_text=found.get('line1', '역대급 해외 바이럴'),
        line2_text=found.get('line2', '웃긴 모먼트 TOP5'),
        sub_text=found.get('sub', '(다들 몇 번이 제일 웃김? ㅋㅋㅋ)'),
        bottom_caption=found.get('caption', '아니 이건 진짜 레전드네 ㅋㅋㅋ 🤣')
    )

    # 3. 디스코드로 배달
    success = send_to_discord(reels_path, found, webhook_url=url)
    if success:
        save_processed_id(found['id'])

    # 4. 완전 무인 모드일 경우 인스타그램으로 승인 없이 즉시 다이렉트 업로드
    auto_ig = os.getenv("AUTO_INSTAGRAM_UPLOAD", "true").lower() == "true"
    if auto_ig:
        try:
            print("🚀 [완전 무인 모드] 인스타그램 릴스 자동 즉시 업로드 진행 중...")
            from instagram_uploader import upload_reels_to_instagram
            res = upload_reels_to_instagram(reels_path)
            # 디스코드 채널로 업로드 성공 알림 전송
            send_to_discord(reels_path, found, channel_id=DEFAULT_CHANNEL_ID, webhook_url=url)
            print(f"✓ 인스타 자동 업로드 완료: {res['url']}")
        except Exception as e:
            print(f"⚠️ 인스타 자동 업로드 실패: {e}")

    print("==========================================")
    print("🎉 무인 배달 완료!")
    print("==========================================")

if __name__ == "__main__":
    cli_webhook = sys.argv[1] if len(sys.argv) > 1 else None
    run_auto_delivery(cli_webhook)
