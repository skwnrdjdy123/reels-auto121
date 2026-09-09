import os
import sys
import json
import random
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
SESSION_TXT_FILE = BASE_DIR / "instagram_session.txt"

# 인스타그램 알고리즘 탐색 탭 노출을 극대화하는 태그 풀
VIRAL_TAGS = [
    "#릴스", "#인스타릴스", "#릴스추천", "#reels", "#reelsinstagram",
    "#유머", "#웃긴영상", "#짤", "#밈", "#도파민", "#유머스타그램",
    "#현웃", "#웃참실패", "#공감", "#개꿀잼", "#심심할때", "#킬링타임",
    "#viral", "#funny", "#memes", "#explorepage", "#fyp"
]

ANIMAL_TAGS = [
    "#고양이", "#강아지", "#댕댕이", "#냥스타그램", "#댕스타그램",
    "#귀여운동물", "#동물짤", "#웃긴동물", "#cuteanimals", "#funnycats"
]

def generate_viral_caption(title: str, sub_question: str = None) -> str:
    """
    인스타그램 알고리즘 도달률과 참여도(댓글/팔로우)를 극대화하는 맞춤형 캡션을 생성합니다.
    """
    if not sub_question:
        sub_question = random.choice([
            "다들 몇 번이 제일 웃김? ㅋㅋㅋ 댓글로 알려줘요 👇",
            "이거 보고 현웃 터진 사람 손 ㅋㅋㅋ ✋",
            "끝까지 보면 반전 실화냐고 ㅋㅋㅋ 🤦‍♂️",
            "친구 태그해서 같이 쪼갤 사람 소환 📢"
        ])

    # 영상 제목에 '고양이', '강아지', '동물'이 들어가면 동물 태그 자동 믹스
    selected_tags = list(VIRAL_TAGS)
    if any(k in title for k in ["고양이", "강아지", "동물", "냥", "댕", "cat", "dog", "pet"]):
        selected_tags.extend(ANIMAL_TAGS)

    random.shuffle(selected_tags)
    hashtag_str = " ".join(selected_tags[:18])

    caption = (
        f"{title} ㅋㅋㅋ 🤣\n\n"
        f"{sub_question}\n\n"
        f"지구 반대편에서 실시간으로 터진 릴스만 엄선해서 배달합니다 📦🇺🇸\n"
        f"👉 @1day_dopami 팔로우하고 매일 도파민 충전하세요 ⚡\n\n"
        f".\n.\n.\n"
        f"{hashtag_str}"
    )
    return caption

def get_instagram_credentials():
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

def login_instagram() -> Client:
    cl = Client()
    cl.delay_range = [1, 3]

    session_id = os.getenv("INSTAGRAM_SESSION_ID")
    if not session_id and SESSION_TXT_FILE.exists():
        session_id = SESSION_TXT_FILE.read_text().strip()

    if session_id:
        try:
            print(f"🔑 sessionid로 인스타그램 로그인 시도 중...")
            cl.login_by_sessionid(session_id)
            cl.dump_settings(SESSION_FILE)
            print("✓ sessionid로 인스타그램 로그인 성공!")
            return cl
        except Exception as e:
            print(f"⚠️ sessionid 로그인 실패, 계정 정보로 폴백: {e}")

    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            print("✓ 기존 세션 재사용 성공!")
            return cl
        except Exception:
            pass

    username, password = get_instagram_credentials()
    if username and password:
        print(f"🔑 인스타그램 계정(@{username}) 로그인 시도 중...")
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("✓ 신규 로그인 및 세션 저장 완료!")
        return cl

    raise ValueError("인스타그램 로그인 정보가 없습니다.")

def upload_reels_to_instagram(video_path: str, title: str = "역대급 해외 바이럴 ㅋㅋㅋ", caption: str = None) -> dict:
    """
    최적화된 해시태그와 함께 릴스를 인스타그램에 자동 업로드합니다.
    """
    if caption is None:
        caption = generate_viral_caption(title)

    print(f"\n🚀 인스타그램 릴스 업로드 시작: {video_path}")
    print(f"📝 적용된 캡션 및 해시태그:\n{caption[:120]}...\n")

    cl = login_instagram()

    media = cl.clip_upload(
        path=video_path,
        caption=caption
    )

    media_id = media.id
    code = media.code
    post_url = f"https://www.instagram.com/reel/{code}/"
    print(f"🎉 릴스 업로드 성공! 링크: {post_url}")

    return {
        "success": True,
        "media_id": media_id,
        "code": code,
        "url": post_url
    }

if __name__ == "__main__":
    sample_caption = generate_viral_caption("역대급 웃긴 고양이 모먼트 랭킹 TOP5")
    print("생성된 캡션 샘플:\n")
    print(sample_caption)
