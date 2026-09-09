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
def generate_human_scene_captions(title: str, duration: float) -> list[dict]:
    """
    레퍼런스 쇼츠(인기 랭킹 및 대세 바이럴)와 100% 동일한 초고속 템포 자막 & 파격적 밈 연출:
    - 자막이 1.6초 ~ 2.0초마다 바로바로 지나가며 시선을 계속 붙잡음!
    - 15~25초 영상 기준 7~12개의 찰진 밈/리액션 자막이 쉴 틈 없이 전개!
    - 각 자막 전환마다 10종 유명 쇼츠 효과음(Whoosh, Pop, Bonk, Boing, Ding, Glitch, Buzzer, Boom, Scratch, Camera)이 리드미컬하게 꽂힘!
    """
    title_lower = title.lower()

    # 1. 쇼츠 특유의 파격적이고 찰진 리액션/상황 멘트 풀 (단계별 빌드업)
    # [1단계: 도입 0~3초] - 시선 강탈 & 호기심 유발
    intro_pool = [
        "처음엔 다들 그냥 장난인 줄 앎ㅋㅋ",
        "시작부터 각도 심상치 않음;;",
        "슬슬 시동 걸기 시작하는데...",
        "여기서 갑자기 이걸 던진다고??",
        "초반부터 텐션 미쳐버림ㅋㅋㅋ",
        "자세 잡는 거부터 예사롭지 않음ㄷㄷ",
        "이때까진 다들 평화로웠음ㅋㅋ"
    ]

    # [2단계: 전개 3~9초] - 긴장감 고조 & 찰진 해설
    if any(k in title_lower for k in ["fail", "clumsy", "regret", "caught", "실수", "레전드"]):
        buildup_pool = [
            "바람 부는데 왜 하필 지금임?ㅋㅋ",
            "친구 세워두고 각 재는 중;;",
            "실수하면 바로 응급실행ㄷㄷ",
            "이게 왜 여기서 꺾이냐고ㅋㅋㅋ",
            "순간 타이밍 놓칠까 봐 조마조마함",
            "친구 표정 슬슬 굳어가는 중ㅋㅋㅋ",
            "저 각도에서 저게 들어간다고??",
            "보는 내가 다 식은땀 남;;"
        ]
    elif any(k in title_lower for k in ["dog", "cat", "pet", "animal", "고양이", "강아지"]):
        buildup_pool = [
            "눈치 살살 보면서 각 재는 중ㅋㅋ",
            "살금살금 다가오는 발걸음 봐ㅋㅋ",
            "저 눈빛은 이미 결심한 눈빛임ㄷㄷ",
            "혼자 진지해서 더 웃김ㅋㅋㅋ",
            "갑자기 왜 저러는지 아는 사람??",
            "순간 엉뚱한 데로 튀어버림ㅋㅋㅋ"
        ]
    else:
        buildup_pool = [
            "자세 잡는 게 진짜 진심이다ㄷㄷ",
            "이 타이밍에 저걸 시도한다고??",
            "주변 사람들도 슬슬 긴장함ㅋㅋ",
            "이게 왜 진짜 되는 거냐고ㅋㅋㅋ",
            "숨죽이고 보게 되는 긴장감;;"
        ]

    # [3단계: 절정/반전 9~15초] - 대폭소 & 뇌정지 리액션
    climax_pool = [
        "순간 다 같이 뇌정지 옴ㅋㅋㅋ",
        "보고도 안 믿김 실화냐ㄷㄷ",
        "이게 되네?? ㅋㅋㅋㅋ",
        "옆 사람 턱 빠지기 직전ㅋㅋㅋ",
        "진짜 숨도 못 쉬고 봄ㅋㅋㅋ",
        "표정 하나로 상황 종결ㅋㅋㅋ",
        "이 타이밍에 이게 터진다고??",
        "웃겨서 숨 넘어갈 뻔함ㅋㅋㅋ",
        "현실 당황한 거 다 티 남ㅋㅋㅋ"
    ]

    # [4단계: 결말 15초~끝] - 레전드 박제 & 인터랙션 유도
    outro_pool = [
        "마지막 표정이 진짜 킬포임ㅋㅋㅋ",
        "결말 보고 현실 웃음 터짐ㅋㅋㅋ",
        "이건 평생 박제감이다ㅋㅋㅋ",
        "외국인들 댓글 난리 난 이유ㅋㅋㅋ",
        "다들 몇 번이 젤 레전드임? 댓글 ㄱㄱ",
        "오늘 하루 중 제일 크게 웃음ㅋㅋㅋ"
    ]

    # 2. 1.8초 단위 고속 전환 타임스탬프 분할
    step_duration = 1.8
    total_steps = max(3, int(duration / step_duration))
    
    # 10종 효과음 순환 믹스 (지루함 0%, 전환 타격감 극대화)
    sfx_cycle = [
        "whoosh", "pop", "camera", "bonk", "boing", 
        "glitch", "ding", "buzzer", "scratch", "boom"
    ]
    random.shuffle(intro_pool)
    random.shuffle(buildup_pool)
    random.shuffle(climax_pool)
    random.shuffle(outro_pool)

    captions = []
    intro_idx = 0
    build_idx = 0
    climax_idx = 0
    outro_idx = 0

    for i in range(total_steps):
        s = round(i * step_duration, 2)
        e = round(min(duration, (i + 1) * step_duration), 2)
        if s >= duration:
            break

        progress = i / max(1, total_steps - 1)
        if progress < 0.25:
            # 1단계 도입
            text = intro_pool[intro_idx % len(intro_pool)]
            intro_idx += 1
            sfx = sfx_cycle[i % len(sfx_cycle)]
        elif progress < 0.65:
            # 2단계 전개
            text = buildup_pool[build_idx % len(buildup_pool)]
            build_idx += 1
            sfx = sfx_cycle[i % len(sfx_cycle)]
        elif progress < 0.88:
            # 3단계 절정
            text = climax_pool[climax_idx % len(climax_pool)]
            climax_idx += 1
            sfx = sfx_cycle[i % len(sfx_cycle)]
        else:
            # 4단계 결말
            text = outro_pool[outro_idx % len(outro_pool)]
            outro_idx += 1
            sfx = "boom" if i == total_steps - 1 else sfx_cycle[i % len(sfx_cycle)]

        captions.append({
            "text": text,
            "start": s,
            "end": e,
            "sfx": sfx
        })

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
                    
                    # 실제로 다운로드 가능한 유효 영상인지 사전 검증 (오류 영상 탐색 원천 제외)
                    try:
                        v_info = ydl.extract_info(v_url, download=False)
                        if not v_info:
                            continue
                        v_dur = v_info.get('duration') or 0
                        if v_dur < 5 or v_dur > 60:
                            save_processed_id(v_id)
                            continue
                    except Exception as err:
                        print(f"다운로드 불가 영상 사전 제외 ({v_id}): {err}")
                        save_processed_id(v_id)
                        continue

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

                # 실제로 다운로드 가능한 유효 영상인지 사전 검증 (오류 영상 탐색 원천 제외)
                try:
                    v_info = ydl.extract_info(v_url, download=False)
                    if not v_info:
                        continue
                    v_dur = v_info.get('duration') or 0
                    if v_dur < 5 or v_dur > 60:
                        save_processed_id(v_id)
                        continue
                except Exception as err:
                    print(f"다운로드 불가 영상 사전 제외 ({v_id}): {err}")
                    save_processed_id(v_id)
                    continue

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
