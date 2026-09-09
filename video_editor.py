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

    # 인스타그램 릴스 Safe Zone 최적화 비디오 영역
    # 상단 헤더 400px 제외한 Y: 400 ~ 1920 (높이 1520)
    VIDEO_AREA_H = 1520
    VIDEO_START_Y = 400

    filters = [
        # 1. 배경용 영상: 1080x1520으로 채우고 부드러운 가우시안 블러 처리
        "[0:v]split=2[bg_raw][fg_raw]",
        f"[bg_raw]scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=increase,crop={TARGET_WIDTH}:{VIDEO_AREA_H},boxblur=30:5,eq=brightness=-0.18[bg_video]",
        # 2. 전경 영상: 1080x1520 영역 내에 비율 완벽 유지하며 중앙 배치
        f"[fg_raw]scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=decrease[fg_video]",
        # 3. 배경 위에 전경을 정중앙 오버레이
        "[bg_video][fg_video]overlay=(W-w)/2:(H-h)/2[video_merged]",
        # 4. 전체 1080x1920 블랙 캔버스에 비디오를 Y=400 위치에 올림
        f"color=c=black:s={TARGET_WIDTH}x{TARGET_HEIGHT}:r={FPS}[base_canvas]",
        f"[base_canvas][video_merged]overlay=0:{VIDEO_START_Y}[canvas_with_video]"
    ]

    cmd_inputs = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-i", overlay_image_path
    ]

    # --- 비디오 필터 구성 ---
    if caption_items:
        filters.append("[canvas_with_video][1:v]overlay=0:0[v_hdr]")
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
        filters.append("[canvas_with_video][1:v]overlay=0:0[v_out]")

    # --- 오디오 효과음(SFX) 믹싱 구성 ---
    from config import SFX_DIR
    audio_sfx_inputs = []
    audio_filters = []
    
    # 원본 오디오를 44.1kHz 스테레오로 정규화
    audio_filters.append("[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.0[a_base]")

    current_input_idx = cmd_inputs.count("-i")  # 정확한 다음 입력 스트림 인덱스
    sfx_count = 0
    sfx_mix_tags = ["[a_base]"]

    if caption_items:
        for cap in caption_items:
            sfx_name = cap.get('sfx')
            if not sfx_name:
                continue
            sfx_file = SFX_DIR / f"{sfx_name}.wav"
            if not sfx_file.exists():
                # pop이나 whoosh 기본 효과음으로 대체
                sfx_file = SFX_DIR / "pop.wav"

            if sfx_file.exists():
                cmd_inputs.extend(["-i", str(sfx_file)])
                delay_ms = int(cap.get('start', 0.0) * 1000)
                sfx_tag = f"a_sfx_{sfx_count}"
                # 효과음 딜레이 및 볼륨 조절
                vol = 0.85 if sfx_name in ["whoosh", "pop"] else 0.75
                audio_filters.append(
                    f"[{current_input_idx}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
                    f"adelay={delay_ms}|{delay_ms},volume={vol}[{sfx_tag}]"
                )
                sfx_mix_tags.append(f"[{sfx_tag}]")
                current_input_idx += 1
                sfx_count += 1

    if sfx_count > 0:
        inputs_str = "".join(sfx_mix_tags)
        # amix로 원본 오디오와 효과음들을 깔끔하게 합성
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

    print(f"✓ 렌더링 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    print("비디오 에디터 준비 완료")
