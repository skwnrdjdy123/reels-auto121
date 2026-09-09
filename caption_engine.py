import re
import random
from pathlib import Path
from deep_translator import GoogleTranslator
from video_analyzer import analyze_video_highlights

# 바이럴 쇼츠 주요 액션/사물 영한 사전 (번역 API 오류 시 완벽 폴백)
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
    "parrot": "앵무새",
    "bicycle": "자전거",
    "bike": "자전거",
    "motorcycle": "오토바이",
    "bottle flip": "물병 세우기",
    "prank": "장난",
    "magic": "마술",
    "drone": "드론",
    "bowling": "볼링",
    "golf": "골프",
    "soccer": "축구",
    "basketball": "농구",
    "dance": "댄스",
    "ice": "빙판길",
    "snow": "눈썰매",
    "roller coaster": "롤러코스터",
    "jump": "점프",
    "climb": "등반",
    "parkour": "파쿠르"
}

def clean_and_translate_title(raw_title: str) -> tuple[str, str]:
    """
    영상 제목에서 불필요한 해시태그/특수기호를 제거하고
    한국어로 정밀 번역하여 실제 상황 키워드를 추출합니다.
    """
    cleaned = re.sub(r'#\S+', '', raw_title)
    cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', cleaned)
    cleaned = cleaned.replace('|', ' ').replace('~', ' ').replace('-', ' ').strip()
    
    noise_words = ["shorts", "tiktok", "viral", "funny", "meme", "2024", "2023", "2025", "best", "compilation", "try not to laugh", "impossible", "fails", "fail"]
    pattern = re.compile(r'\b(' + '|'.join(noise_words) + r')\b', re.IGNORECASE)
    cleaned_sub = pattern.sub('', cleaned).strip()
    cleaned = cleaned_sub if cleaned_sub else cleaned

    title_lower = raw_title.lower()

    # 오프라인 사전 매칭
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
    유튜브 쇼츠 상위 1% 초고속 템포 예능 밈(Meme) 스타일 자막 & 효과음 동기화 엔진:
    - 0.9초 ~ 1.4초 스피디한 템포로 화면 중앙에 즉각적(Pop-up)으로 자막 꽂힘
    - 설명조 자막 완전 배제, 센스 넘치는 예능형 펀치라인 자막 (예: "저기서 저걸?", "눈치 챙겨...", "대참사 ㅋㅋㅋ")
    - 사건이 터지는 정확한 0.1초 시점에 하이라이트 자막과 타격 효과음(퍽!, 찰싹!, 띠용~, 윈도우 에러, 관객 웃음) 직격
    - 하이라이트 줌인 연출용 메인 피크 타임스탬프 산출
    """
    # 1. 비디오/오디오 AI 물리 분석 (컷 및 30ms Onset 오디오 피크)
    analysis = analyze_video_highlights(video_path, duration)
    cuts = analysis["cuts"]
    peaks = analysis["peaks"]

    translated_title, action_ctx = clean_and_translate_title(title)
    print(f"🎬 [예능 밈 분석] 제목: '{translated_title}' | 핵심 키워드: '{action_ctx}'", flush=True)

    # 2. 쇼츠 유행 예능/밈 펀치라인 자막 풀 (짧고 굵은 시선 강탈형)
    # [1단계: 훅/도입 0~20%] - 시선 집중 & 어이없는 시작
    hook_templates = [
        f"저기서 {action_ctx}을?? ㅋㅋㅋ",
        "눈치 챙겨... 제발 ㅋㅋㅋ",
        "시작부터 자세가 불안함 ㄷㄷ",
        "벌써부터 쎄한 느낌 옴 ;;",
        "자신감만 100단 장착함 ㅋㅋ",
        "이때까진 다들 평화로웠음 ㅋㅋ",
        "저러다 일 터질 텐데... ;;"
    ]

    # [2단계: 빌드업/전개 20~55%] - 긴장감 고조 & 황당함
    buildup_templates = [
        "각 재는 것 봐라 ㅋㅋㅋㅋ",
        "설마 했는데 진짜로...?",
        "안 돼 멈춰!! ㅋㅋㅋㅋ",
        "보는 내가 다 조마조마함 ㄷㄷ",
        "친구 표정 슬슬 굳어짐 ㅋㅋ",
        "거리 계산 완벽(?)하게 하는 중",
        "여기서 뇌정지 오기 3초 전 ;;"
    ]

    # [3단계: 사건 폭발/피크 (피크 터지는 0.1초 순간!)] - 촌철살인 펀치라인
    climax_templates = [
        "대참사 ㅋㅋㅋㅋㅋ",
        "퍽!! ㅋㅋㅋㅋㅋ",
        "순간 뇌정지 옴 ㅋㅋㅋ",
        "어이 가출 실화냐 ㄷㄷ",
        "그걸 왜 쳐 ㅋㅋㅋㅋ",
        "물리법칙 무시 레전드 ㅋㅋㅋ",
        "결국 터져버림 ㅋㅋㅋㅋ",
        "보고도 안 믿김 ㄷㄷ"
    ]

    # [4단계: 리액션/결말 70%~끝] - 현실 폭소 & 여운
    outro_templates = [
        "표정 실화냐 ㅋㅋㅋㅋ",
        "영혼 탈곡 완료 ㅋㅋㅋ",
        "평생 이불킥 확정 ㅋㅋㅋ",
        "외국인들도 기겁한 결말 ㅋㅋㅋ",
        "웃겨서 숨 넘어감 ㅋㅋㅋㅋ",
        "무한 재생하게 만드네 ㅋㅋㅋ"
    ]

    random.shuffle(hook_templates)
    random.shuffle(buildup_templates)
    random.shuffle(climax_templates)
    random.shuffle(outro_templates)

    # 3. 칼같은 스피디한 자막 타임라인 계산 (1.0초 ~ 1.4초 템포)
    # 사건이 터지는 피크 순간(peak)은 0.1초 오차 없이 자막 시작점으로 고정!
    anchors = set([0.0])
    for p in peaks:
        if 0.5 <= p <= duration - 0.8:
            anchors.add(round(p, 2))
    for c in cuts:
        if 0.6 <= c <= duration - 0.8:
            anchors.add(round(c, 2))

    sorted_anchors = sorted(list(anchors))

    # 1.0초 ~ 1.4초 간격으로 촘촘히 쪼개어 스피디한 예능 호흡 유지
    final_timestamps = [0.0]
    for nxt in sorted_anchors[1:]:
        gap = nxt - final_timestamps[-1]
        if gap > 1.6:
            num_sub = int(gap / 1.2)
            step = gap / (num_sub + 1)
            for s_idx in range(1, num_sub + 1):
                final_timestamps.append(round(final_timestamps[-1] + step, 2))
        elif gap < 0.7:
            continue
        final_timestamps.append(round(nxt, 2))

    if duration - final_timestamps[-1] > 1.3:
        final_timestamps.append(round(duration - 1.1, 2))

    final_timestamps = sorted(list(set(final_timestamps)))

    # 4. 자막 아이템 매핑
    captions = []
    hook_i = 0
    build_i = 0
    climax_i = 0
    outro_i = 0

    for i in range(len(final_timestamps)):
        start_t = final_timestamps[i]
        end_t = round(final_timestamps[i + 1], 2) if i + 1 < len(final_timestamps) else round(duration, 2)
        if start_t >= duration:
            break

        progress = start_t / max(1.0, duration)
        # 현재 시점이 오디오 피크(사건 발생 0.1초 순간)인지 확인
        is_peak_moment = any(abs(start_t - p) <= 0.25 for p in peaks)

        if is_peak_moment and progress >= 0.25:
            # 사건 터지는 정확한 순간: "대참사 ㅋㅋㅋ", "퍽!! ㅋㅋㅋ" 펀치라인 팍!
            text = climax_templates[climax_i % len(climax_templates)]
            climax_i += 1
        elif progress < 0.22 and i < 2:
            text = hook_templates[hook_i % len(hook_templates)]
            hook_i += 1
        elif progress < 0.70:
            text = buildup_templates[build_i % len(buildup_templates)]
            build_i += 1
        else:
            text = outro_templates[outro_i % len(outro_templates)]
            outro_i += 1

        captions.append({
            "text": text,
            "start": start_t,
            "end": end_t
        })

    # 5. 타격감 있는 밈(Meme) 효과음 타임라인 (정확한 0.1초 타격 시점)
    raw_sfx_events = []

    # (1) 영상 시작 인트로 슉!
    raw_sfx_events.append({"time": 0.0, "sfx": "whoosh", "vol": 2.8})

    # (2) 오디오 피크 시점 (퍽!, 찰싹!, 띠용~, 윈도우 에러, 관객 웃음)
    main_peak_time = None
    if peaks:
        main_peak_time = peaks[0]  # 가장 큰 충격/하이라이트 순간

        # 첫 번째 메인 피크: 강력한 퍽! (bonk/punch)
        raw_sfx_events.append({"time": peaks[0], "sfx": "punch", "vol": 3.4})
        
        # 메인 피크 0.4초 뒤 관객 폭소/웃음소리 연타 (하하하!)
        laugh_time = round(peaks[0] + 0.45, 2)
        if laugh_time < duration - 0.8:
            raw_sfx_events.append({"time": laugh_time, "sfx": "laugh", "vol": 3.0})

        # 그 외 피크들: 찰싹, 띠용, 윈도우 에러
        sfx_pool = ["slap", "boing", "windows_error", "buzzer", "ding"]
        for p_idx, p_time in enumerate(peaks[1:], start=1):
            if p_time < 0.4 or p_time > duration - 0.6:
                continue
            choice_sfx = sfx_pool[(p_idx - 1) % len(sfx_pool)]
            raw_sfx_events.append({"time": p_time, "sfx": choice_sfx, "vol": 3.2})

    # (3) 시각적 컷 전환 시점
    for c_time in cuts:
        if 0.5 <= c_time <= duration - 1.0:
            if not any(abs(c_time - ev["time"]) < 0.5 for ev in raw_sfx_events):
                raw_sfx_events.append({"time": c_time, "sfx": random.choice(["pop", "camera"]), "vol": 2.6})

    # (4) 엔딩 클라이맥스 쿵!
    end_sfx_t = round(duration - 0.9, 2)
    if end_sfx_t > 2.0 and not any(abs(end_sfx_t - ev["time"]) < 0.6 for ev in raw_sfx_events):
        raw_sfx_events.append({"time": end_sfx_t, "sfx": "boom", "vol": 3.0})

    # 정렬 및 0.4초 간격 필터링
    raw_sfx_events.sort(key=lambda x: x["time"])
    sfx_events = []
    last_t = -999.0
    for ev in raw_sfx_events:
        if ev["time"] - last_t >= 0.4:
            sfx_events.append(ev)
            last_t = ev["time"]

    print(f"🔥 [초스피디 예능 밈 자막] 총 {len(captions)}개 자막 생성 (평균 1.2초 템포)")
    print(f"🔊 [타격감 밈 효과음] 총 {len(sfx_events)}개 매핑 (메인 하이라이트 피크: {main_peak_time}초)")

    return {
        "captions": captions,
        "sfx_events": sfx_events,
        "main_peak_time": main_peak_time
    }
