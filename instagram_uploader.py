import os
import sys
import json
from pathlib import Path
from instagrapi import Client
from config import BASE_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SESSION_FILE = BASE_DIR / "ig_session.json"
ACCOUNT_FILE = BASE_DIR / "instagram_account.json"

def get_instagram_credentials():
    """인스타그램 아이디/비밀번호 가져오기"""
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username and ACCOUNT_FILE.exists():
        try:
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                username = data.get("username")
                password = data.get("password")
        except Exception:
            pass

    return username, password

SESSION_TXT_FILE = BASE_DIR / "instagram_session.txt"

def login_instagram() -> Client:
    """인스타그램 세션 쿠키(sessionid) 또는 계정 정보로 로그인"""
    cl = Client()
    cl.delay_range = [1, 3]

    # 1. 환경변수 또는 파일에서 sessionid 가져오기 (1초 무인증 로그인)
    session_id = os.getenv("INSTAGRAM_SESSION_ID")
    if not session_id and SESSION_TXT_FILE.exists():
        session_id = SESSION_TXT_FILE.read_text().strip()

    if session_id:
        try:
            print(f"🔑 sessionid로 인스타그램 로그인 시도 중...")
            cl.login_by_sessionid(session_id)
            cl.dump_settings(SESSION_FILE)
            print("✓ sessionid로 인스타그램 로그인 대성공!")
            return cl
        except Exception as e:
            print(f"⚠️ sessionid 로그인 실패, 계정 정보로 폴백 시도: {e}")

    # 2. 기존 저장된 세션 파일 재사용
    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            print("✓ 기존 인스타그램 세션 재사용 성공!")
            return cl
        except Exception:
            pass

    # 2. 신규 로그인
    print(f"🔑 인스타그램 계정(@{username}) 로그인 시도 중...")
    cl.login(username, password)
    cl.dump_settings(SESSION_FILE)
    print("✓ 인스타그램 신규 로그인 및 세션 저장 완료!")
    return cl

def upload_reels_to_instagram(video_path: str, caption: str = None) -> dict:
    """
    완성된 mp4 비디오를 인스타그램 릴스로 자동 업로드합니다.
    """
    if caption is None:
        caption = (
            "다들 몇 번이 제일 웃김? ㅋㅋㅋ 🤣\n"
            "팔로우하고 매일 도파민 충전하세요! ⚡\n\n"
            "#릴스 #유머 #쇼츠 #웃긴영상 #짤 #밈 #추천 #fyp #reels"
        )

    print(f"\n🚀 인스타그램 릴스 업로드 시작: {video_path}")
    cl = login_instagram()

    media = cl.clip_upload(
        path=video_path,
        caption=caption
    )

    media_id = media.id
    code = media.code
    post_url = f"https://www.instagram.com/reel/{code}/"
    print(f"🎉 릴스 업로드 대성공!")
    print(f"🔗 게시물 링크: {post_url}")

    return {
        "success": True,
        "media_id": media_id,
        "code": code,
        "url": post_url
    }

if __name__ == "__main__":
    u, p = get_instagram_credentials()
    if u and p:
        print(f"설정된 인스타그램 계정: @{u}")
    else:
        print("인스타그램 계정 설정이 필요합니다.")
