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

    # 랭킹 스타일 문구 분리
    line1_options = [
        "역대급 웃긴 순간",
        "역대급 해외 바이럴",
        "역대급 레전드 모먼트",
        "실시간 떡상 중인",
        "해외에서 난리 난"
    ]
    line1_text = random.choice(line1_options)
    line2_text = f"{translated[:14]} 모먼트" if len(translated) > 4 else "모먼트 랭킹 TOP5"
    sub_text = random.choice([
        "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)",
        "(마지막 결말 실화냐고 ㅋㅋㅋ)",
        "(웃참 실패하면 팔로우 ㅋㅋㅋ)",
        "(댓글 반응 폭발함 ㅋㅋㅋ)"
    ])
    bottom_caption = random.choice(REACTION_PHRASES)

    return line1_text, line2_text, sub_text, bottom_caption

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
                if v_duration and v_duration > 65:
                    continue

                v_url = f"https://www.youtube.com/shorts/{v_id}"
                v_title = entry.get('title', 'Viral Short')

                print(f"🎯 신규 바이럴 영상 발견: {v_title} ({v_url})")
                line1, line2, sub, caption = generate_korean_hook(v_title)

                return {
                    'id': v_id,
                    'url': v_url,
                    'orig_title': v_title,
                    'line1': line1,
                    'line2': line2,
                    'sub': sub,
                    'caption': caption,
                    # 기존 호환용
                    'top_title': f"{line1} {line2}",
                    'bottom_text': caption
                }

    raise RuntimeError("새로운 바이럴 영상을 찾지 못했습니다. 잠시 후 다시 시도해 주세요.")

if __name__ == "__main__":
    found = find_viral_video()
    print("탐색 결과:", found)
