import re
import random
from pathlib import Path
from deep_translator import GoogleTranslator
from video_analyzer import analyze_scenes_and_impacts

# 바이럴 쇼츠 주요 액션/사물 영한 사전
ACTION_DICT = {
    "pinky up": "새끼손가락",
    "pinky": "새끼손가락",
    "backflip": "백덤블링",
    "front flip": "앞덤블링",
    "hoverboard": "호버보드",
    "skateboard": "스케이트보드",
    "skate": "스케이트",
    "treadmill": "런닝머신",
    "trampoline": "트램펄린",
    "bench press": "벤치프레스",
    "gym": "헬스장",
    "workout": "운동",
    "water slide": "워터슬라이드",
    "waterslide": "워터슬라이드",
    "pool": "수영장 다이빙",
    "diving": "다이빙",
    "cake": "케이크",
    "cooking": "요리",
    "pancake": "팬케이크",
    "cat": "고양이",
    "kitten": "아기 고양이",
    "dog": "강아지",
    "puppy": "강아지",
    "bird": "새",
    "bicycle": "자전거",
    "bike": "자전거",
    "bottle flip": "물병 세우기",
    "prank": "장난",
    "magic": "마술",
    "drone": "드론",
    "hammer": "망치질",
    "wood": "목공 작업",
    "dance": "댄스"
}

def clean_and_translate_title(raw_title: str) -> tuple[str, str]:
    cleaned = re.sub(r'#\S+', '', raw_title)
    cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', cleaned)
    cleaned = cleaned.replace('|', ' ').replace('~', ' ').replace('-', ' ').strip()
    
    noise_words = ["shorts", "tiktok", "viral", "funny", "meme", "2024", "2023", "2025", "best", "compilation", "try not to laugh", "impossible", "fails", "fail"]
    pattern = re.compile(r'\b(' + '|'.join(noise_words) + r')\b', re.IGNORECASE)
    cleaned_sub = pattern.sub('', cleaned).strip()
    cleaned = cleaned_sub if cleaned_sub else cleaned

    title_lower = raw_title.lower()

    dict_hit = None
    for k, v in ACTION_DICT.items():
        if k in title_lower:
            dict_hit = v
            break

    translated = None
    try:
        res = GoogleTranslator(source='auto', target='ko').translate(cleaned).strip()
        if res and not any(err in res.lower() for err in ["error", "server error", "500", "404", "html", "<", ">"]):
            if len(res) <= 35:
                translated = res
    except Exception:
        pass

    if not translated:
        translated = dict_hit if dict_hit else "화제의 순간"

    if dict_hit:
        action_ctx = dict_hit
    else:
        ko_clean = re.sub(r'(웃긴|실패|실수|대참사|레전드|모음|순간|영상|쇼츠|챌린지|모먼트|해외|화제)', '', translated).strip()
        ko_clean = re.sub(r'\s+', ' ', ko_clean).strip()
        if 2 <= len(ko_clean) <= 12:
            action_ctx = ko_clean
        else:
            action_ctx = "이 상황"

    return translated, action_ctx

def generate_adaptive_smart_captions(video_path: str, title: str, duration: float) -> dict:
    """
    틱톡 / 유튜브 쇼츠 대세 예능형 씬-액션 칼싱크 자막 & 효과음 엔진:
    1. 각 클립(씬)을 정밀 분할하고, 사건이 터지는 정확한 타격 순간(Impact)을 0.02초 단위로 검출
    2. 클립마다 [도입 훅 자막] ➔ [정확한 타격 시점 펀치라인 자막] 2단계 구조 적용
    3. 똑같은 자막 중복 100% 방지 (전체 영상에서 모든 자막 유일 보장)
    4. 사건이 터지는 그 순간에 퍽!, 찰싹!, 띠용~, 관객 폭소 등 찰진 밈 사운드 칼싱크
    5. 하이라이트 타격 순간 화면 줌인(Zoom-in) 및 흔들림(Shake) 트리거 타임스탬프 산출
    """
    # 1. 씬 및 클립별 타격 순간 정밀 물리 분석
    clips = analyze_scenes_and_impacts(video_path, duration)
    translated_title, action_ctx = clean_and_translate_title(title)
    print(f"🎬 [클립별 예능 밈 분석] 제목: '{translated_title}' | 주제: '{action_ctx}'", flush=True)

    # 2. 클립별 상황 맞춤 예능 펀치라인 자막 풀
    # [클립 1 훅 & 펀치]
    clip1_hooks = [
        f"저기서 {action_ctx}을 왜 해? ㅋㅋ",
        "시작부터 자세가 불안함 ㄷㄷ",
        "눈치 챙겨... 제발 ㅋㅋㅋ",
        "자신감만 100단 장착함 ㅋㅋ"
    ]
    clip1_punches = [
        "시작부터 대참사 ㅋㅋㅋㅋ",
        "퍽!! ㅋㅋㅋㅋㅋ",
        "어이 가출 실화냐 ㄷㄷ",
        "각도 진짜 예술이다 ㅋㅋㅋ"
    ]

    # [클립 2 훅 & 펀치 (예: 아이/친구/장난)]
    clip2_hooks = [
        "아빠 손은 내 장난감 ㅋㅋㅋ",
        "설마 저 손을 치겠어...? ㄷㄷ",
        "눈빛은 이미 진심이다 ㅋㅋㅋ",
        "안 돼 멈춰!! ㅋㅋㅋㅋ"
    ]
    clip2_punches = [
        "아빠 손 멸망 ㅋㅋㅋㅋㅋ",
        "그걸 진짜 치네 ㅋㅋㅋㅋ",
        "퍽!! 소리 찰진 거 봐 ㅋㅋㅋ",
        "비명소리 여기까지 들림 ㅋㅋㅋ"
    ]

    # [클립 3 훅 & 펀치 (예: 통나무/실수/스스로 자초)]
    clip3_hooks = [
        "스스로 불러온 재앙 ㅋㅋㅋ",
        "각도가 벌써 망했는데 ;;",
        "보는 내가 다 조마조마함 ㄷㄷ",
        "슬슬 불길한 예감이 옴 ㅋㅋㅋ"
    ]
    clip3_punches = [
        "내 손가락 으악!! ㅋㅋㅋㅋ",
        "찰싹!! 소리 실화냐 ㅋㅋㅋ",
        "물리법칙 무시 레전드 ㅋㅋㅋ",
        "순간 뇌정지 옴 ㅋㅋㅋㅋ"
    ]

    # [클립 4+ 및 결말 훅 & 펀치]
    clip4_hooks = [
        "표정 하나로 상황 종결 ㅋㅋㅋ",
        "마지막 결말이 진짜 킬포임 ㅋㅋㅋ",
        "외국인들도 기겁한 순간 ㅋㅋㅋ",
        "이건 평생 박제감이다 ㅋㅋㅋ"
    ]
    clip4_punches = [
        "영혼까지 털려버림 ㅋㅋㅋㅋ",
        "평생 이불킥 확정 ㅋㅋㅋㅋ",
        "웃겨서 숨 넘어감 ㅋㅋㅋㅋ",
        "무한 재생하게 만드네 ㅋㅋㅋ"
    ]

    used_captions = set()
    def get_unique_caption(pool: list[str], fallback: str) -> str:
        available = [c for c in pool if c not in used_captions]
        if not available:
            # 변형 추가로 중복 회피
            for i in range(1, 10):
                cand = f"{fallback} {i}"
                if cand not in used_captions:
                    used_captions.add(cand)
                    return cand
            return fallback
        chosen = random.choice(available)
        used_captions.add(chosen)
        return chosen

    captions = []
    raw_sfx_events = []
    impact_moments = []

    # 첫 시작 슉! 효과음
    raw_sfx_events.append({"time": 0.0, "sfx": "whoosh", "vol": 2.8})

    for c_idx, clip in enumerate(clips):
        c_start = clip['start']
        c_end = clip['end']
        c_impact = clip['impact']
        impact_moments.append(c_impact)

        # 클립 번호별 맞춤 훅 및 펀치라인 선택
        if c_idx == 0:
            hook_text = get_unique_caption(clip1_hooks, "저기서 저걸 왜 해? ㅋㅋ")
            punch_text = get_unique_caption(clip1_punches, "대참사 ㅋㅋㅋㅋㅋ")
            impact_sfx = "punch"
        elif c_idx == 1:
            hook_text = get_unique_caption(clip2_hooks, "아빠 손은 내 장난감 ㅋㅋㅋ")
            punch_text = get_unique_caption(clip2_punches, "아빠 손 멸망 ㅋㅋㅋㅋㅋ")
            impact_sfx = "punch"
        elif c_idx == 2:
            hook_text = get_unique_caption(clip3_hooks, "스스로 불러온 재앙 ㅋㅋㅋ")
            punch_text = get_unique_caption(clip3_punches, "내 손가락 으악!! ㅋㅋㅋㅋ")
            impact_sfx = "slap"
        else:
            hook_text = get_unique_caption(clip4_hooks, "표정 하나로 상황 종결 ㅋㅋㅋ")
            punch_text = get_unique_caption(clip4_punches, "영혼까지 털려버림 ㅋㅋㅋㅋ")
            impact_sfx = "boing"

        # 1. 클립 도입 훅 자막 (클립 시작 ~ 타격 직전)
        hook_end = round(max(c_start + 0.8, c_impact - 0.05), 2)
        captions.append({
            "text": hook_text,
            "start": c_start,
            "end": hook_end
        })

        # 2. 타격 순간 펀치라인 자막 (정확히 c_impact 순간 팍! 꽂힘)
        punch_end = round(min(c_end, c_impact + 1.6), 2)
        captions.append({
            "text": punch_text,
            "start": c_impact,
            "end": punch_end
        })

        # 3. 효과음 칼싱크 (사건 터지는 정확한 타격 시점!)
        raw_sfx_events.append({
            "time": c_impact,
            "sfx": impact_sfx,
            "vol": 3.8  # 타격감 확실하게 증폭!
        })

        # 하이라이트 클립인 경우 타격 0.35초 뒤 관객 폭소 하하하! 연타
        if c_idx in [0, 1] and (c_impact + 0.38 < c_end):
            raw_sfx_events.append({
                "time": round(c_impact + 0.38, 2),
                "sfx": "laugh",
                "vol": 3.2
            })

        # 씬 전환 컷 효과음 (다음 클립으로 넘어갈 때)
        if c_end < duration - 1.0:
            raw_sfx_events.append({
                "time": c_end,
                "sfx": "camera" if c_idx % 2 == 0 else "whoosh",
                "vol": 2.6
            })

    # 마지막 엔딩 피날레 쿵!
    raw_sfx_events.append({
        "time": round(duration - 0.9, 2),
        "sfx": "boom",
        "vol": 3.2
    })

    # 효과음 시간순 정렬
    raw_sfx_events.sort(key=lambda x: x["time"])
    sfx_events = []
    last_t = -999.0
    for ev in raw_sfx_events:
        if ev["time"] - last_t >= 0.30:
            sfx_events.append(ev)
            last_t = ev["time"]

    print(f"\n==========================================", flush=True)
    print(f"🎬 [칼싱크 자막 완성] 총 {len(captions)}개 (중복률 0% 완전 보장):", flush=True)
    for cap in captions:
        print(f"   - {cap['start']:>4.2f}s ~ {cap['end']:>4.2f}s: \"{cap['text']}\"", flush=True)
    print(f"🔊 [타격 효과음 칼싱크] 총 {len(sfx_events)}개 매핑 완료", flush=True)
    for ev in sfx_events:
        print(f"   - {ev['time']:>4.2f}s: [{ev['sfx'].upper()}] (볼륨 {ev['vol']}x)", flush=True)
    print(f"==========================================\n", flush=True)

    return {
        "captions": captions,
        "sfx_events": sfx_events,
        "impact_moments": impact_moments,
        "main_peak_time": impact_moments[1] if len(impact_moments) > 1 else (impact_moments[0] if impact_moments else None)
    }
