import os
import subprocess
import uuid
from config import TARGET_WIDTH, TARGET_HEIGHT, FPS, OUTPUT_DIR

def render_reels(
    input_video_path: str,
    overlay_image_path: str,
    caption_items: list[dict] = None,
    output_filename: str = None,
    sfx_events: list[dict] = None,
    highlight_peak: float = None
) -> str:
    """
    유튜브 쇼츠 / 틱톡 최상위 예능 및 밈(Meme) 스타일 릴스 렌더링 엔진:
    - 1080x1920 세로 풀해상도 (9:16)
    - 상단 고정 헤더 배너 (두꺼운 고딕 + 흰색 볼드 + 검은색 외곽선)
    - 화면 중앙부(Y: 1080) 큼직한 70px 예능 펀치라인 자막 오버레이
    - 하이라이트 순간(사건 폭발/타격) 화면 1.2배 순간 확대(Punch Zoom-in) & 흔들림(Camera Shake) 연출
    - 퍽!, 찰싹!, 띠용~, 윈도우 에러, 관객 웃음소리 등 고타격감 밈 사운드 밀리초 믹싱
    """
    if output_filename is None:
        unique_id = uuid.uuid4().hex[:8]
        output_filename = f"reels_{unique_id}.mp4"
    
    output_path = str(OUTPUT_DIR / output_filename)

    # 원본 영상 해상도 확인
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        input_video_path
    ]
    is_vertical = False
    try:
        res = subprocess.check_output(probe_cmd, text=True).strip()
        if "x" in res:
            w, h = map(int, res.split("x")[:2])
            if h > w * 1.2:
                is_vertical = True
    except Exception as e:
        print(f"해상도 측정 실패: {e}")

    # 하이라이트 순간 펀치 줌(Punch Zoom) & 셰이크(Camera Shake) 필터 수식 구성
    punch_zoom_filter = ""
    if highlight_peak and highlight_peak > 0.5:
        p_s = round(highlight_peak, 2)
        p_e = round(highlight_peak + 0.45, 2)
        # 피크 순간에 1.22배 확대 및 미세 흔들림
        punch_zoom_filter = (
            f",crop=w='if(between(t,{p_s},{p_e}),in_w/1.22,in_w)':"
            f"h='if(between(t,{p_s},{p_e}),in_h/1.22,in_h)':"
            f"x='(in_w-out_w)/2 + if(between(t,{p_s},{p_e}),sin(t*60)*6,0)':"
            f"y='(in_h-out_h)/2 + if(between(t,{p_s},{p_e}),cos(t*60)*6,0)'"
        )
        print(f"🎬 [화면 연출] {p_s}초 ~ {p_e}초 구간 순간 줌인(Punch Zoom) & 흔들림(Shake) 장착!", flush=True)

    if is_vertical:
        # 이미 세로 쇼츠인 경우
        filters = [
            f"[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop={TARGET_WIDTH}:{TARGET_HEIGHT}{punch_zoom_filter},scale={TARGET_WIDTH}:{TARGET_HEIGHT}[v_full]",
        ]
        base_video_tag = "v_full"
    else:
        # 가로 영상(16:9) 또는 정사각형 원본인 경우
        VIDEO_AREA_H = 1040
        VIDEO_START_Y = 400
        filters = [
            "[0:v]split=2[bg_raw][fg_raw]",
            f"[bg_raw]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop={TARGET_WIDTH}:{TARGET_HEIGHT},boxblur=40:5,eq=brightness=-0.35[bg_video]",
            f"[fg_raw]scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=decrease{punch_zoom_filter},scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=decrease[fg_video]",
            f"color=c=black:s={TARGET_WIDTH}x{TARGET_HEIGHT}:r={FPS}[base_canvas]",
            f"[bg_video][fg_video]overlay=(W-w)/2:{VIDEO_START_Y}[video_centered]",
            f"[base_canvas][video_centered]overlay=0:0[canvas_with_video]"
        ]
        base_video_tag = "canvas_with_video"

    cmd_inputs = [
        "ffmpeg", "-y",
        "-i", input_video_path
    ]

    cmd_inputs.extend(["-i", overlay_image_path])
    if caption_items:
        filters.append(f"[{base_video_tag}][1:v]overlay=0:0[v_hdr]")
        last_tag = "v_hdr"
        for idx, cap in enumerate(caption_items, start=2):
            cmd_inputs.extend(["-i", cap['image_path']])
            is_last = (idx == len(caption_items) + 1)
            next_tag = "v_out" if is_last else f"v_cap{idx}"
            s = cap.get('start', 0.0)
            e = cap.get('end', 999.0)
            # 페이드인 없이 즉각 팝업(Pop-up) 전환
            filters.append(f"[{last_tag}][{idx}:v]overlay=0:0:enable='between(t,{s},{e})'[{next_tag}]")
            last_tag = next_tag
    else:
        filters.append(f"[{base_video_tag}][1:v]overlay=0:0[v_out]")

    # --- 오디오 효과음(SFX) 믹싱 구성 ---
    from config import SFX_DIR
    audio_filters = []
    current_input_idx = cmd_inputs.count("-i")
    sfx_count = 0
    sfx_mix_tags = []

    # 효과음 볼륨 매핑 (타격감 극대화)
    sfx_vol_map = {
        "punch": 3.5,
        "bonk": 3.4,
        "slap": 3.4,
        "boing": 3.2,
        "windows_error": 3.2,
        "laugh": 3.0,
        "boom": 3.0,
        "ding": 3.0,
        "whoosh": 2.8,
        "pop": 2.8,
        "camera": 2.8,
        "buzzer": 2.8,
        "glitch": 2.8,
        "scratch": 2.8
    }

    target_sfx_list = []
    if sfx_events:
        for ev in sfx_events:
            target_sfx_list.append({
                "time": ev.get("time", 0.0),
                "sfx": ev.get("sfx", "pop"),
                "vol": ev.get("vol", sfx_vol_map.get(ev.get("sfx"), 3.0))
            })
    elif caption_items:
        for cap in caption_items:
            if cap.get('sfx'):
                target_sfx_list.append({
                    "time": cap.get('start', 0.0),
                    "sfx": cap.get('sfx'),
                    "vol": sfx_vol_map.get(cap.get('sfx'), 3.0)
                })

    for item in target_sfx_list:
        sfx_name = item.get('sfx', 'pop')
        sfx_file = SFX_DIR / f"{sfx_name}.wav"
        if not sfx_file.exists():
            sfx_file = SFX_DIR / "pop.wav"

        if sfx_file.exists():
            cmd_inputs.extend(["-i", str(sfx_file)])
            sfx_tag = f"a_sfx_{sfx_count}"
            delay_ms = int(item.get('time', 0.0) * 1000)
            vol = float(item.get('vol', sfx_vol_map.get(sfx_name, 3.0)))
            audio_filters.append(
                f"[{current_input_idx}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
                f"adelay={delay_ms}|{delay_ms},volume={vol}[{sfx_tag}]"
            )

            sfx_mix_tags.append(f"[{sfx_tag}]")
            current_input_idx += 1
            sfx_count += 1

    if sfx_count > 0:
        # 원본 사운드를 0.65로 약간 정돈하고, 효과음이 확실하게 터지도록 믹싱
        audio_filters.insert(0, "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=0.65[a_base]")
        inputs_str = "[a_base]" + "".join(sfx_mix_tags)
        audio_filters.append(f"{inputs_str}amix=inputs={sfx_count+1}:duration=first:dropout_transition=0,volume=1.5[a_out]")
        map_audio = "[a_out]"
    else:
        map_audio = "0:a?"

    all_filters = filters + audio_filters
    filter_complex_str = ";".join(all_filters)

    cmd = cmd_inputs + [
        "-filter_complex", filter_complex_str,
        "-map", "[v_out]",
        "-map", map_audio,
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.1",
        "-preset", "veryfast",
        "-crf", "23",
        "-maxrate", "3500k",
        "-bufsize", "7000k",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        output_path
    ]

    print(f"FFmpeg 예능 밈 스타일 릴스 렌더링 시작: {output_path}")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"[SUCCESS] 렌더링 완료: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg 렌더링 실패: {e.stderr.decode('utf-8', errors='replace')}")
        raise
