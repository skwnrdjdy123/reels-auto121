import os
import sys
import json
import random
import yt_dlp
from pathlib import Path
from deep_translator import GoogleTranslator
from config import BASE_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROCESSED_FILE = BASE_DIR / "processed_videos.json"

SEARCH_QUERIES = [
    "#shorts funny memes",
    "#shorts unexpected viral",
    "#shorts funny pets cats dogs",
    "#shorts try not to laugh",
    "#shorts hilarious moments",
    "#shorts instant karma",
    "#shorts meme compilation"
]

REACTION_PHRASES = [
    "반응 진짜 킹받네 ㅋㅋㅋ 🤣",
    "끝까지 보면 반전 주의 ㄷㄷ",
    "외국인들 댓글 난리 남 ㅋㅋㅋ",
    "이게 왜 진짜임? ㅋㅋㅋ",
    "도파민 충전 완료 🚨",
    "아니 결말 실화냐고 ㅋㅋㅋ 🤦‍♂️",
    "웃참 실패 레전드 ㅋㅋㅋ"
]

def load_processed_ids() -> set:
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_id(video_id: str):
    processed = load_processed_ids()
    processed.add(video_id)
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, ensure_ascii=False, indent=2)

def generate_korean_hook(english_title: str) -> tuple[str, str]:
    """
    영문 제목을 번역하고 한국 인스타 릴스에 맞게 후킹 타이틀과 하단 반응 문구를 생성합니다.
    """
    # 해시태그 제거 및 정리
    clean_title = english_title.split('#')[0].strip()
    clean_title = clean_title.replace('|', '').replace('~', '').strip()
    if not clean_title or len(clean_title) < 3:
        clean_title = "재밌는 영상"

    # 번역
    try:
        translator = GoogleTranslator(source='auto', target='ko')
        translated = translator.translate(clean_title)
        if len(translated) > 25:
            translated = translated[:25] + "..."
    except Exception:
        translated = clean_title[:20]

    hook_patterns = [
        f"외국에서 난리 난 {translated} ㅋㅋㅋ",
        f"실시간 해외 떡상 중인 {translated}",
        f"조회수 폭발한 {translated} ㅋㅋㅋ",
        f"{translated} 실화냐 ㅋㅋㅋ"
    ]
    top_title = random.choice(hook_patterns)
    bottom_text = random.choice(REACTION_PHRASES)

    return top_title, bottom_text

def find_viral_video() -> dict:
    """
    해외 유튜브 쇼츠에서 아직 제작하지 않은 인기 바이럴 영상을 1개 탐색하여 반환합니다.
    """
    processed_ids = load_processed_ids()
    random.shuffle(SEARCH_QUERIES)

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for query in SEARCH_QUERIES:
            print(f"🔍 해외 바이럴 영상 탐색 중... (키워드: {query})")
            try:
                search_result = ydl.extract_info(f"ytsearch20:{query}", download=False)
            except Exception:
                continue

            entries = search_result.get('entries', []) if search_result else []

            for entry in entries:
                v_id = entry.get('id')
                if not v_id or v_id in processed_ids:
                    continue

                v_duration = entry.get('duration')
                # 60초 초과 영상 제외 (쇼츠는 최대 60초)
                if v_duration and v_duration > 65:
                    continue

                v_url = f"https://www.youtube.com/shorts/{v_id}"
                v_title = entry.get('title', 'Viral Short')

                print(f"🎯 신규 바이럴 영상 발견: {v_title} ({v_url})")
                top_title, bottom_text = generate_korean_hook(v_title)

                return {
                    'id': v_id,
                    'url': v_url,
                    'orig_title': v_title,
                    'top_title': top_title,
                    'bottom_text': bottom_text
                }

    raise RuntimeError("새로운 바이럴 영상을 찾지 못했습니다. 잠시 후 다시 시도해 주세요.")

if __name__ == "__main__":
    found = find_viral_video()
    print("탐색 결과:", found)
