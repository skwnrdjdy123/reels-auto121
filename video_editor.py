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
    FFmpeg를 사용하여 원본 영상을 9:16 (1080x1920) 릴스로 변환하고
    배경 블러 + 중앙 원본 영상 + 상하단 텍스트 오버레이를 합성합니다.
    """
    if output_filename is None:
        unique_id = uuid.uuid4().hex[:8]
        output_filename = f"reels_{unique_id}.mp4"
    
    output_path = str(OUTPUT_DIR / output_filename)

    # FFmpeg 필터그래프 정의
    # 1. 원본 비디오를 둘로 나눔 [bg_in], [fg_in]
    # 2. bg: 1080x1920으로 꽉 채운 후(crop) 블러(gblur 또는 boxblur) 및 약간 어둡게(eq) 처리
    # 3. fg: 원본 비율 유지하면서 1080x1920 프레임 안에 맞게 스케일
    # 4. bg 위에 fg를 정중앙에 배치
    # 5. 그 위에 overlay.png 오버레이
    filter_complex = (
        "[0:v]split=2[bg_in][fg_in];"
        f"[bg_in]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},boxblur=20:5,eq=brightness=-0.1:saturation=1.1[bg];"
        f"[fg_in]scale={TARGET_WIDTH}:-2:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
        "[merged][1:v]overlay=0:0[v_out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-i", overlay_image_path,
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-map", "0:a?",  # 오디오가 있으면 매핑, 없어도 오류 나지 않게 '?' 사용
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    print(f"FFmpeg 렌더링 실행 중: {output_path}")
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    
    if process.returncode != 0:
        print("FFmpeg 에러 로그:\n", process.stderr[-1000:])
        raise RuntimeError(f"FFmpeg 인코딩 실패 (exit code {process.returncode})")

    print(f"릴스 렌더링 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    print("비디오 에디터 준비 완료")
