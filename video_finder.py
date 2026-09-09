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

# 1. 자막 및 텍스트 없는 해외 순수 원본 밈/동물 바이럴 클립 채널 목록
PRIORITY_CHANNELS = [
    "https://www.youtube.com/@FailArmy/shorts",            # 해외 원본 웃긴 실수/해프닝 클립
    "https://www.youtube.com/@ThePetCollective/shorts",    # 해외 원본 반려동물/동물 클립
    "https://www.youtube.com/@PeopleAreAwesome/shorts",    # 해외 원본 신기한 모먼트
    "https://www.youtube.com/@animalsdoingthings/shorts"   # 해외 원본 동물 행동 클립
]

# 2. 텍스트/자막 없는 순수 해외 원본 영상 검색 쿼리
SEARCH_QUERIES = [
    "funny animal moments original clip",
    "hilarious pet reaction raw footage",
    "instant regret caught on camera original",
    "funny cat moments original video",
    "unexpected dog reaction caught on tape",
    "wholesome animal reaction raw clip",
    "funniest moments caught on camera original",
    "funny fails original video clip"
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

    # 3단계 시간 구간 배분 및 유명 쇼츠 10종 효과음(SFX) 다채로운 매핑
    t1 = round(max(2.5, duration * 0.32), 1)
    t2 = round(max(t1 + 2.5, duration * 0.65), 1)
    t3 = round(max(t2 + 2.5, duration), 1)

    # 1단계 도입 효과음 풀: 빠른 전환 및 시선 집중
    sfx1_candidates = ["whoosh", "camera", "pop"]
    # 2단계 전개 효과음 풀: 재미있는 상황, 실수, 호기심
    if any(k in title_lower for k in ["fail", "clumsy", "regret", "실수"]):
        sfx2_candidates = ["bonk", "boing", "glitch"]
    elif any(k in title_lower for k in ["cat", "dog", "pet", "동물"]):
        sfx2_candidates = ["boing", "pop", "camera"]
    else:
        sfx2_candidates = ["pop", "boing", "bonk"]

    # 3단계 결말/반전 효과음 풀: 레전드 펀치라인, 반전, 감탄
    sfx3_candidates = ["ding", "scratch", "boom", "buzzer"]

    sfx1 = random.choice(sfx1_candidates)
    sfx2 = random.choice(sfx2_candidates)
    sfx3 = random.choice(sfx3_candidates)

    captions = [
        {"text": random.choice(step1_pool), "start": 0.0, "end": t1, "sfx": sfx1},
        {"text": random.choice(step2_pool), "start": t1, "end": t2, "sfx": sfx2},
        {"text": random.choice(step3_pool), "start": t2, "end": t3, "sfx": sfx3}
    ]
    return captions


def generate_korean_hook(english_title: str) -> tuple[str, str, str, str]:
    """
    영상 내용에 맞춤형 훅 타이틀을 생성합니다:
    - 실제로 여러 장면이 들어있는 모음집/컴필레이션인 경우: '역대급 [주제] / 모먼트 랭킹 TOP N'
    - 단일 해프닝/클립 영상인 경우: '역대급 화제 된 [주제] / 실제 반응 레전드 모먼트 / (결말 보고 빵 터짐 ㅋㅋㅋ)'
    """
    clean_title = english_title.split('#')[0].strip()
    clean_title = clean_title.replace('|', '').replace('~', '').strip()
    title_lower = clean_title.lower()

    # 번역
    try:
        translator = GoogleTranslator(source='auto', target='ko')
        translated = translator.translate(clean_title)
    except Exception:
        translated = clean_title

    # 1. 실제 다중 장면 랭킹/모음집 영상인지 확인 (TOP N 또는 compilation 키워드)
    import re
    top_num_match = re.search(r'(?:top|ranking)\s*(\d+)', title_lower)
    is_compilation = bool(top_num_match) or any(w in title_lower for w in ["compilation", "fails compilation", "top 5", "top 6", "top 10", "ranking", "moments compilation"])

    # 2. 주제어 식별
    if any(k in title_lower for k in ["cat", "kitten", "고양이"]):
        topic = "웃긴 고양이"
    elif any(k in title_lower for k in ["dog", "puppy", "강아지", "개"]):
        topic = "웃긴 강아지"
    elif any(k in title_lower for k in ["pet", "animal", "동물"]):
        topic = "귀여운 동물"
    elif any(k in title_lower for k in ["baby", "kid", "child", "아기", "아이"]):
        topic = "귀여운 아이들"
    elif any(k in title_lower for k in ["prank", "장난", "몰카"]):
        topic = "꿀잼 장난"
    elif any(k in title_lower for k in ["fail", "regret", "clumsy", "실수"]):
        topic = "순간포착 레전드"
    else:
        topic = "해외 바이럴"

    # 3. 모음집 vs 단일 클립 분기 처리 (사기 및 괴리감 방지!)
    if is_compilation:
        top_num = f"TOP{top_num_match.group(1)}" if top_num_match else "TOP 5"
        line1_text = f"역대급 {topic}"
        line2_text = f"모먼트 랭킹 {top_num}"
        sub_text = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)"
    else:
        # 단일 클립 영상인 경우: 랭킹 TOP5를 붙이지 않고 단일 상황에 100% 맞는 고몰입 훅 사용
        line1_text = f"역대급 화제 된 {topic}"
        punchlines = [
            "실제 반응 레전드 모먼트",
            "보고도 안 믿기는 실제 상황",
            "웃겨서 난리 난 반응 순간",
            "끝까지 보게 만드는 장면",
            "외국인들 댓글 폭발한 순간"
        ]
        line2_text = random.choice(punchlines)
        sub_quotes = [
            "(결말 보고 현실 웃음 터짐 ㅋㅋㅋ)",
            "(마지막 표정이 진짜 킬포 ㅋㅋㅋ)",
            "(끝까지 보면 이유가 나옴 ㅋㅋㅋ)",
            "(표정 하나로 상황 정리 ㅋㅋㅋ)",
            "(보고만 있어도 힐링 됨 ㅋㅋㅋ)"
        ]
        sub_text = random.choice(sub_quotes)

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
                    
                    # 이미 다른 한국 채널이 편집해 올린 2차 가공 영상(한국어 제목 포함)은 100% 제외
                    korean_chars = sum(1 for c in v_title if '\uac00' <= c <= '\ud7a3')
                    if korean_chars >= 2:
                        continue

                    v_url = f"https://www.youtube.com/shorts/{v_id}"
                    print(f"🔥 [해외 순수 원본 바이럴 클립 발견!] {v_title} ({v_url})")
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
                
                # 이미 편집된 한국어 영상 제외 (순수 외국어 원본만 수집)
                korean_chars = sum(1 for c in v_title if '\uac00' <= c <= '\ud7a3')
                if korean_chars >= 2:
                    continue

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
