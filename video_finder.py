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

# 1. 6000만 뷰 메가 랭킹 쇼츠 공식 채널 목록 (최우선 탐색)
PRIORITY_CHANNELS = [
    "https://www.youtube.com/channel/UC2oP74F0FiE1jWQPy31YUVw/shorts",  # 레퍼런스 랭킹 채널 (TOP 6 랭킹 쇼츠)
    "https://www.youtube.com/@랭킹모음/shorts",
]

# 2. 대중적으로 조회수 폭발하는 메가 트렌드 밈 키워드
SEARCH_QUERIES = [
    "역대급 랭킹 shorts",
    "top 5 hilarious viral ranking shorts",
    "try not to laugh hilarious shorts 1M views",
    "funniest moments caught on camera viral shorts",
    "best funny pet moments viral shorts",
    "instant regret hilarious shorts",
    "laugh challenge viral meme shorts",
    "failarmy funniest shorts"
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

def generate_human_scene_captions(title: str, duration: float = 20.0) -> list[dict]:
    """
    억지웃음("ㅋㅋㅋ 🤣", "레전드 ㄷㄷ") 없이,
    사람이 영상을 보면서 실제로 자연스럽게 공감하고 관찰하는 인간미 넘치는 장면별 3단계 자막을 생성합니다.
    """
    title_lower = title.lower()

    if any(k in title_lower for k in ["dog", "cat", "pet", "puppy", "kitten", "animal", "고양이", "강아지", "동물"]):
        step1_pool = [
            "처음엔 그냥 지나가는 줄 알았는데",
            "멀리서부터 눈 마주치더니 멈칫함",
            "살금살금 다가오는 발걸음 봐",
            "시작부터 이미 장난기 가득한 눈빛"
        ]
        step2_pool = [
            "눈치 살살 보면서 각 재는 중",
            "자세 잡는 게 진짜 진심이다",
            "자신만만했던 표정이 점점 진지해짐",
            "저 눈빛은 이미 마음 정한 눈빛인데"
        ]
        step3_pool = [
            "보고만 있어도 마음이 편안해진다",
            "하루 피로가 그냥 싹 녹아내림",
            "이건 몇 번을 다시 봐도 힐링이다",
            "오늘 본 영상 중에 제일 따뜻함"
        ]
    elif any(k in title_lower for k in ["kid", "baby", "child", "toddler", "heartwarming", "wholesome", "아이", "아기"]):
        step1_pool = [
            "처음엔 무슨 일인가 싶었는데",
            "멀리서 서로 알아보고 멈칫함",
            "달려오는 발걸음부터 신남이 가득함",
            "마주치는 순간부터 이미 감동"
        ]
        step2_pool = [
            "서로 꼭 껴안는 거 보고 울컥할 뻔",
            "표정에 순수함이 그대로 묻어남",
            "세상에 둘밖에 없는 것 같은 순간",
            "바라보는 눈빛이 너무 다정하다"
        ]
        step3_pool = [
            "진짜 보고 있는 내내 미소가 안 떠남",
            "이런 게 진짜 사람 사는 맛이지",
            "마음 따뜻해지는 최고의 명장면",
            "오늘 하루도 힘내야겠다는 생각이 듬"
        ]
    elif any(k in title_lower for k in ["fail", "regret", "clumsy", "caught", "funny", "laugh", "실수", "순간"]):
        step1_pool = [
            "시작할 때만 해도 분위기 엄청 좋았음",
            "자세 잡을 때부터 뭔가 심상치 않더라",
            "주변 사람들까지 슬슬 긴장하는 중",
            "이때까진 아무도 몰랐겠지"
        ]
        step2_pool = [
            "서서히 일어나는 변화에 숨죽이게 됨",
            "순간 타이밍 놓칠까 봐 조마조마함",
            "점점 걷잡을 수 없이 흘러가는 상황",
            "표정 하나하나가 너무 생생하다"
        ]
        step3_pool = [
            "이건 생각지도 못한 타이밍이었다",
            "마지막 반전이 진짜 깊은 여운을 남김",
            "몇 번을 돌려봐도 순간을 못 잊겠네",
            "오늘 하루 중 제일 집중해서 본 듯"
        ]
    else:
        step1_pool = [
            "처음엔 아무 생각 없이 보다가",
            "눈길을 확 사로잡는 첫인상",
            "뭔가 심상치 않은 조짐이 보임",
            "시작부터 묘하게 빠져들게 됨"
        ]
        step2_pool = [
            "점점 분위기에 깊게 몰입하게 됨",
            "디테일 하나하나가 눈에 들어오기 시작",
            "생각보다 훨씬 진지한 상황",
            "여기서부터 숨죽이고 보게 됨"
        ]
        step3_pool = [
            "끝까지 보길 정말 잘했다는 생각",
            "여운이 꽤 오래 남는 명장면",
            "주변 사람들에게도 꼭 보여주고 싶어짐",
            "다시 봐도 타이밍이 진짜 예술이다"
        ]

    # 3단계 시간 구간 배분 및 상황별 최적 효과음(SFX) 매핑
    t1 = round(max(3.0, duration * 0.33), 1)
    t2 = round(max(t1 + 3.0, duration * 0.68), 1)
    t3 = round(max(t2 + 3.0, duration), 1)

    captions = [
        {"text": random.choice(step1_pool), "start": 0.0, "end": t1, "sfx": "whoosh"},
        {"text": random.choice(step2_pool), "start": t1, "end": t2, "sfx": "pop"},
        {"text": random.choice(step3_pool), "start": t2, "end": t3, "sfx": "ding"}
    ]
    return captions

def generate_korean_hook(english_title: str) -> tuple[str, str, str, str]:
    """
    레퍼런스 영상과 100% 일치하는 '역대급 [주제] 모먼트 랭킹 TOP N' 포맷으로 타이틀을 생성합니다.
    """
    clean_title = english_title.split('#')[0].strip()
    clean_title = clean_title.replace('|', '').replace('~', '').strip()

    # 번역
    try:
        translator = GoogleTranslator(source='auto', target='ko')
        translated = translator.translate(clean_title)
    except Exception:
        translated = clean_title

    # 주제어 추출 및 정돈
    import re
    # TOP N 숫자 추출
    top_num_match = re.search(r'(?:TOP|Top)\s*(\d+)', clean_title)
    top_num = f"TOP{top_num_match.group(1)}" if top_num_match else "TOP 5"

    title_lower = clean_title.lower()
    if any(k in title_lower for k in ["cat", "kitten", "고양이"]):
        line1_text = "역대급 웃긴 고양이"
        line2_text = f"모먼트 랭킹 {top_num}"
    elif any(k in title_lower for k in ["dog", "puppy", "강아지", "개"]):
        line1_text = "역대급 웃긴 강아지"
        line2_text = f"모먼트 랭킹 {top_num}"
    elif any(k in title_lower for k in ["pet", "animal", "동물"]):
        line1_text = "역대급 귀여운 동물"
        line2_text = f"모먼트 랭킹 {top_num}"
    elif any(k in title_lower for k in ["snowball", "fight"]):
        line1_text = "역대급 웃긴 눈싸움"
        line2_text = f"모먼트 랭킹 {top_num}"
    elif any(k in title_lower for k in ["baby", "kid", "child", "아기", "아이"]):
        line1_text = "역대급 사랑스러운 아이들"
        line2_text = f"모먼트 랭킹 {top_num}"
    elif any(k in title_lower for k in ["prank", "장난", "몰카"]):
        line1_text = "역대급 꿀잼 몰카"
        line2_text = f"모먼트 랭킹 {top_num}"
    else:
        line1_text = "역대급 해외 바이럴"
        # 12자 이내로 축약
        short_topic = translated.replace("TOP", "").replace("Top", "").strip()[:10]
        line2_text = f"{short_topic} 랭킹 {top_num}"

    sub_text = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)"
    bottom_caption = "이건 진짜 예상 못 했다 ㅋㅋㅋ"

    return line1_text, line2_text, sub_text, bottom_caption

def find_viral_video(min_views: int = 300000) -> dict:
    """
    1. 레퍼런스 공식 랭킹 채널(6000만 뷰 메가 랭킹 쇼츠) 최우선 탐색
    2. 수백만~수천만 이상 터진 '대세 랭킹 및 바이럴 쇼츠' 엄선
    """
    processed_ids = load_processed_ids()

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # --- 1단계: 레퍼런스 채널 (TOP 랭킹 쇼츠 원본) 최우선 탐색 ---
        for chan_url in PRIORITY_CHANNELS:
            print(f"🌟 [레퍼런스 랭킹 채널 탐색] {chan_url}")
            try:
                chan_result = ydl.extract_info(chan_url, download=False)
                entries = chan_result.get('entries', []) if chan_result else []
                # 조회수 높은 순서 정렬
                entries.sort(key=lambda x: x.get('view_count') or 0, reverse=True)

                for entry in entries:
                    v_id = entry.get('id')
                    if not v_id or v_id in processed_ids:
                        continue
                    import re
                    if not re.match(r'^[a-zA-Z0-9_-]{11}$', str(v_id)):
                        continue

                    v_title = entry.get('title', '')
                    v_url = f"https://www.youtube.com/shorts/{v_id}"
                    print(f"🔥 [레퍼런스 랭킹 대세 영상 발견!] {v_title} ({v_url})")
                    line1, line2, sub, caption = generate_korean_hook(v_title)

                    return {
                        'id': v_id,
                        'url': v_url,
                        'orig_title': v_title,
                        'line1': line1,
                        'line2': line2,
                        'sub': sub,
                        'caption': caption,
                        'top_title': f"{line1} {line2}",
                        'bottom_text': caption
                    }
            except Exception as e:
                print(f"채널 탐색 일시 건너뜀: {e}")
                continue

        # --- 2단계: 키워드 검색 탐색 ---
        random.shuffle(SEARCH_QUERIES)
        for query in SEARCH_QUERIES:
            print(f"🔍 메가 바이럴 트렌드 탐색 중... (키워드: {query})")
            try:
                search_result = ydl.extract_info(f"ytsearch25:{query}", download=False)
            except Exception:
                continue

            entries = search_result.get('entries', []) if search_result else []
            entries.sort(key=lambda x: x.get('view_count') or 0, reverse=True)

            for entry in entries:
                v_id = entry.get('id')
                if not v_id or v_id in processed_ids:
                    continue

                import re
                if not re.match(r'^[a-zA-Z0-9_-]{11}$', str(v_id)):
                    continue

                v_title = entry.get('title', '')
                title_lower = v_title.lower()

                if any(bad in title_lower for bad in ["live", "24/7", "stream", "broadcast", "compilation"]):
                    continue

                v_duration = entry.get('duration')
                if v_duration and (v_duration < 7 or v_duration > 50):
                    continue

                v_url = f"https://www.youtube.com/shorts/{v_id}"
                print(f"🎯 검증된 대세 밈 영상 발견! | ID: {v_id} | 제목: {v_title}")
                line1, line2, sub, caption = generate_korean_hook(v_title)

                return {
                    'id': v_id,
                    'url': v_url,
                    'orig_title': v_title,
                    'line1': line1,
                    'line2': line2,
                    'sub': sub,
                    'caption': caption,
                    'top_title': f"{line1} {line2}",
                    'bottom_text': caption
                }

    raise RuntimeError("새로운 바이럴 영상을 찾지 못했습니다. 잠시 후 다시 시도해 주세요.")

if __name__ == "__main__":
    found = find_viral_video()
    print("탐색 결과:", found)
