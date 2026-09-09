import random
from video_analyzer import analyze_video_highlights

def generate_adaptive_smart_captions(video_path: str, title: str, duration: float) -> list[dict]:
    """
    영상 컷(I-Frame) 및 오디오 피크(웃음/타격/고함)를 물리적으로 감지하여
    하이라이트와 중요한 순간에 100% 싱크되는 고성능 자막 & 효과음 타임라인을 생성합니다.
    """
    # 1. 비디오/오디오 AI 분석 실행
    analysis = analyze_video_highlights(video_path, duration)
    cuts = analysis["cuts"]
    peaks = analysis["peaks"]

    title_lower = title.lower()

    # 2. 파격적이고 찰진 상황별 쇼츠 자막 풀 (감정 단계별)
    # [훅/도입] (0~3초)
    hook_pool = [
        "처음엔 다들 그냥 장난인 줄 앎ㅋㅋ",
        "시작부터 각도 심상치 않음;;",
        "슬슬 시동 걸기 시작하는데...",
        "여기서 갑자기 이걸 던진다고??",
        "초반부터 텐션 미쳐버림ㅋㅋㅋ",
        "자세 잡는 거부터 예사롭지 않음ㄷㄷ",
        "이때까진 다들 평화로웠음ㅋㅋ",
        "눈치 살살 보면서 각 재는 중ㅋㅋ"
    ]

    # [빌드업/전개] (3~10초)
    if any(k in title_lower for k in ["fail", "clumsy", "regret", "caught", "실수", "레전드"]):
        buildup_pool = [
            "바람 부는데 왜 하필 지금임?ㅋㅋ",
            "친구 세워두고 사격 중;;",
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

    # [하이라이트/피크] (피크 순간 꽂히는 펀치라인 자막)
    peak_pool = [
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

    # [엔딩/피날레] (마지막 3초)
    outro_pool = [
        "마지막 표정이 진짜 킬포임ㅋㅋㅋ",
        "결말 보고 현실 웃음 터짐ㅋㅋㅋ",
        "이건 평생 박제감이다ㅋㅋㅋ",
        "외국인들 댓글 난리 난 이유ㅋㅋㅋ",
        "다들 몇 번이 젤 레전드임? 댓글 ㄱㄱ",
        "오늘 하루 중 제일 크게 웃음ㅋㅋㅋ"
    ]

    random.shuffle(hook_pool)
    random.shuffle(buildup_pool)
    random.shuffle(peak_pool)
    random.shuffle(outro_pool)

    # 3. 주요 전환점(Anchor Timestamps) 통합: 시작(0.0), 컷들, 오디오 피크들
    raw_anchors = set([0.0])
    for c in cuts:
        if 0.8 <= c <= duration - 1.2:
            raw_anchors.add(round(c, 2))
    for p in peaks:
        if 0.8 <= p <= duration - 1.2:
            raw_anchors.add(round(p, 2))

    sorted_anchors = sorted(list(raw_anchors))

    # 4. 시간 간격이 너무 벌어진 구간(2.3초 이상)은 중간 자막으로 촘촘히 보강
    final_timestamps = [0.0]
    for nxt in sorted_anchors[1:]:
        gap = nxt - final_timestamps[-1]
        if gap > 2.5:
            num_sub = int(gap / 1.8)
            step = gap / (num_sub + 1)
            for s_idx in range(1, num_sub + 1):
                final_timestamps.append(round(final_timestamps[-1] + step, 2))
        elif gap < 1.2:
            continue  # 너무 짧은 간격은 스킵
        final_timestamps.append(round(nxt, 2))

    # 마지막 구간 처리
    if duration - final_timestamps[-1] > 2.2:
        final_timestamps.append(round(duration - 1.8, 2))

    final_timestamps = sorted(list(set(final_timestamps)))

    # 5. 타임라인 매핑 및 스마트 효과음 앵커링
    captions = []
    hook_i = 0
    build_i = 0
    peak_i = 0
    outro_i = 0

    peak_set = set([round(p, 1) for p in peaks])
    cut_set = set([round(c, 1) for c in cuts])

    for i in range(len(final_timestamps)):
        start_t = final_timestamps[i]
        end_t = round(final_timestamps[i + 1], 2) if i + 1 < len(final_timestamps) else round(duration, 2)
        if start_t >= duration:
            break

        progress = start_t / max(1.0, duration)
        
        # 현재 타이밍이 오디오 피크(큰 소리/웃음/쿵)나 컷인지 확인
        is_audio_peak = any(abs(start_t - p) <= 0.3 for p in peaks)
        is_cut = any(abs(start_t - c) <= 0.25 for c in cuts)

        # 도입부(0~3초)는 우선적으로 훅 자막을 사용
        if progress < 0.18 and i < 2:
            text = hook_pool[hook_i % len(hook_pool)]
            hook_i += 1
            sfx = random.choice(["whoosh", "pop", "camera"])
        elif is_audio_peak and progress >= 0.35:
            # 중반 이후 하이라이트/피크 순간: 뇌정지/충격 멘트 + 강력한 펀치 SFX (Bonk, Boom, Buzzer, Ding, Glitch)
            text = peak_pool[peak_i % len(peak_pool)]
            peak_i += 1
            sfx = random.choice(["bonk", "boom", "ding", "buzzer", "glitch"])
        elif is_cut:
            # 장면 전환 순간: 시선 전환 SFX (Whoosh, Camera, Pop)
            text = buildup_pool[build_i % len(buildup_pool)]
            build_i += 1
            sfx = random.choice(["whoosh", "camera", "pop", "scratch"])
        elif progress < 0.75:
            text = buildup_pool[build_i % len(buildup_pool)]
            build_i += 1
            sfx = random.choice(["pop", "boing", "bonk", "glitch"])
        else:
            text = outro_pool[outro_i % len(outro_pool)]
            outro_i += 1
            sfx = "boom" if i == len(final_timestamps) - 1 else random.choice(["ding", "whoosh", "boom"])

        captions.append({
            "text": text,
            "start": start_t,
            "end": end_t,
            "sfx": sfx
        })

    return captions
