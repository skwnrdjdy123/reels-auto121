import os
import subprocess
import uuid
from config import TARGET_WIDTH, TARGET_HEIGHT, FPS, OUTPUT_DIR

def render_reels(
    input_video_path: str,
    overlay_image_path: str,
    caption_items: list = None,
    output_filename: str = None
) -> str:
    """
    유튜브 랭킹 숏폼 스타일 및 인스타그램 릴스 최적화 화면으로 렌더링합니다:
    - 1080x1920 규격 (9:16)
    - 상단 400px 인스타 Safe Zone 고정 헤더
    - 중앙 1520px 공간에 원본 영상 (블러 배경 + 중앙 원본)
    - 하단 Safe Zone(Y:1370)에 장면별로 자연스럽게 전환되는 인간미 자막 오버레이
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
            if h > w * 1.2:  # 이미 세로 쇼츠 영상인 경우
                is_vertical = True
    except Exception as e:
        print(f"해상도 측정 실패: {e}")

    if is_vertical:
        # 이미 세로 쇼츠인 경우:
        # 영상을 억지로 축소시켜 위아래/양옆에 검은 여백을 만들지 않고, 1080x1920 풀화면으로 배치!
        # 기존 영상 내 텍스트와 겹치는 상단 헤더/하단 자막은 중복 삽입하지 않거나 최소화합니다.
        filters = [
            f"[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop={TARGET_WIDTH}:{TARGET_HEIGHT}[v_full]",
        ]
        base_video_tag = "v_full"
    else:
        # 가로 영상(16:9) 또는 정사각형 원본인 경우 (이상적인 밈/클립 소스):
        # 상단 400px 헤더바 + 중앙 비디오(가로) + 하단 여백 자막바
        # 자막이 원본 영상을 절대 가리지 않고 하단 검은 여백에 깔끔하게 들어감!
        VIDEO_AREA_H = 1000
        VIDEO_START_Y = 420
        filters = [
            "[0:v]split=2[bg_raw][fg_raw]",
            f"[bg_raw]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop={TARGET_WIDTH}:{TARGET_HEIGHT},boxblur=40:5,eq=brightness=-0.35[bg_video]",
            f"[fg_raw]scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=decrease[fg_video]",
            f"color=c=black:s={TARGET_WIDTH}x{TARGET_HEIGHT}:r={FPS}[base_canvas]",
            f"[bg_video][fg_video]overlay=(W-w)/2:{VIDEO_START_Y}[video_centered]",
            f"[base_canvas][video_centered]overlay=0:0[canvas_with_video]"
        ]
        base_video_tag = "canvas_with_video"


    cmd_inputs = [
        "ffmpeg", "-y",
        "-i", input_video_path
    ]

    # --- 비디오 필터 구성 ---
    if is_vertical:
        # 이미 세로 쇼츠인 경우: 자막과 헤더가 이미 영상 자체에 있으므로 가림 방지를 위해 추가 덧씌움 없이 원본 100% 보존
        filters.append(f"[{base_video_tag}]null[v_out]")
    else:
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
                filters.append(f"[{last_tag}][{idx}:v]overlay=0:0:enable='between(t,{s},{e})'[{next_tag}]")
                last_tag = next_tag
        else:
            filters.append(f"[{base_video_tag}][1:v]overlay=0:0[v_out]")



    # --- 오디오 효과음(SFX) 믹싱 구성 ---
    from config import SFX_DIR
    audio_sfx_inputs = []
    audio_filters = []
    
    # 원본 오디오를 44.1kHz 스테레오로 정규화
    # 원본 오디오를 44.1kHz 스테레오로 정규화
    audio_filters = []
    current_input_idx = cmd_inputs.count("-i")
    sfx_count = 0
    sfx_mix_tags = []

    if caption_items and not is_vertical:
        for cap in caption_items:
            sfx_name = cap.get('sfx')
            if not sfx_name:
                continue
            sfx_file = SFX_DIR / f"{sfx_name}.wav"
            if not sfx_file.exists():
                sfx_file = SFX_DIR / "pop.wav"

            if sfx_file.exists():
                cmd_inputs.extend(["-i", str(sfx_file)])
                delay_ms = int(cap.get('start', 0.0) * 1000)
                sfx_tag = f"a_sfx_{sfx_count}"
                vol = 0.85 if sfx_name in ["whoosh", "pop"] else 0.75
                audio_filters.append(
                    f"[{current_input_idx}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
                    f"adelay={delay_ms}|{delay_ms},volume={vol}[{sfx_tag}]"
                )
                sfx_mix_tags.append(f"[{sfx_tag}]")
                current_input_idx += 1
                sfx_count += 1

    if sfx_count > 0:
        audio_filters.insert(0, "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.0[a_base]")
        inputs_str = "[a_base]" + "".join(sfx_mix_tags)
        audio_filters.append(f"{inputs_str}amix=inputs={sfx_count+1}:duration=first:dropout_transition=0,volume=1.6[a_out]")
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
        "-crf", "20",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
        "-shortest",
        output_path
    ]

    print(f"FFmpeg 랭킹 스타일 및 효과음 믹싱 릴스 렌더링 시작: {output_path}")
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    
    if process.returncode != 0:
        print("FFmpeg 에러 로그:\n", process.stderr[-1000:])
        raise RuntimeError(f"FFmpeg 인코딩 실패 (exit code {process.returncode})")

    print(f"[SUCCESS] 렌더링 완료: {output_path}")
    return output_path


if __name__ == "__main__":
    print("비디오 에디터 준비 완료")
