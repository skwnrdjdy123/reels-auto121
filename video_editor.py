import os
import subprocess
import uuid
from config import TARGET_WIDTH, TARGET_HEIGHT, FPS, OUTPUT_DIR

def render_reels(
    input_video_path: str,
    overlay_image_path: str,
    output_filename: str = None
) -> str:
    """
    유튜브 랭킹 숏폼 스타일로 릴스를 렌더링합니다:
    - 1080x1920 규격
    - 상단 480px는 고정 블랙 헤더 (핑크 1줄 + 화이트 2줄 + 서브텍스트)
    - 하단 480~1920 영역에 원본 영상 (블러 배경 + 중앙 원본)
    - 상단 헤더 및 하단 자막 오버레이 결합
    """
    if output_filename is None:
        unique_id = uuid.uuid4().hex[:8]
        output_filename = f"reels_{unique_id}.mp4"
    
    output_path = str(OUTPUT_DIR / output_filename)

    # 비디오 영역: 너비 1080, 높이 1440 (Y: 480 ~ 1920)
    VIDEO_AREA_H = 1440
    VIDEO_START_Y = 480

    filter_complex = (
        # 1. 배경용 영상: 1080x1440으로 채우고 블러 처리
        "[0:v]split=2[bg_raw][fg_raw];"
        f"[bg_raw]scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{VIDEO_AREA_H},boxblur=25:5,eq=brightness=-0.15[bg_video];"
        # 2. 전경 영상: 1080x1440 영역 내에 비율 유지하며 축소
        f"[fg_raw]scale={TARGET_WIDTH}:{VIDEO_AREA_H}:force_original_aspect_ratio=decrease[fg_video];"
        # 3. 배경 위에 전경을 중앙 오버레이
        f"[bg_video][fg_video]overlay=(W-w)/2:(H-h)/2[video_merged];"
        # 4. 전체 1080x1920 블랙 캔버스에 비디오를 Y=480 위치에 올림
        f"color=c=black:s={TARGET_WIDTH}x{TARGET_HEIGHT}:r={FPS}[base_canvas];"
        f"[base_canvas][video_merged]overlay=0:{VIDEO_START_Y}[canvas_with_video];"
        # 5. 그 위에 1080x1920 헤더 및 자막 오버레이 합성
        "[canvas_with_video][1:v]overlay=0:0[v_out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-i", overlay_image_path,
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    print(f"FFmpeg 랭킹 스타일 릴스 렌더링 시작: {output_path}")
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    
    if process.returncode != 0:
        print("FFmpeg 에러 로그:\n", process.stderr[-1000:])
        raise RuntimeError(f"FFmpeg 인코딩 실패 (exit code {process.returncode})")

    print(f"✓ 렌더링 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    print("비디오 에디터 준비 완료")
