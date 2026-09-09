import os
import sys
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from downloader import download_video
from banner_maker import create_text_overlay
from video_editor import render_reels

def create_reels_pipeline(
    video_url: str,
    top_title: str = None,
    bottom_text: str = None
) -> str:
    """
    영상 URL에서 다운로드부터 한글 배너 생성, 9:16 릴스 합성까지 전체 자동화 파이프라인
    """
    print(f"\n==========================================")
    print(f"🎬 해외 바이럴 릴스 자동 제작 시작!")
    print(f"🔗 영상 URL: {video_url}")
    print(f"==========================================")

    # 1. 비디오 다운로드
    print("\n[1/3] 비디오 다운로드 중...")
    video_info = download_video(video_url)
    raw_video_path = video_info['file_path']
    orig_title = video_info['title']
    print(f"✓ 원본 다운로드 완료: {orig_title} ({raw_video_path})")

    # 2. 타이틀 설정 (입력값이 없으면 기본 유머 후킹 타이틀 생성)
    if not top_title:
        top_title = f"외국에서 난리 난 {orig_title[:20]} ㅋㅋㅋ"
    if not bottom_text:
        bottom_text = "끝까지 보면 소름 돋음 🤣"

    # 3. 텍스트 배너 이미지 생성
    print(f"\n[2/3] 한글 배너 이미지 생성 중...")
    print(f"   - 상단 제목: {top_title}")
    print(f"   - 하단 반응: {bottom_text}")
    overlay_path = create_text_overlay(
        top_title=top_title,
        bottom_text=bottom_text
    )
    print(f"✓ 배너 이미지 생성 완료: {overlay_path}")

    # 4. FFmpeg 9:16 릴스 렌더링
    print("\n[3/3] FFmpeg 릴스 합성 및 인코딩 중...")
    output_path = render_reels(
        input_video_path=raw_video_path,
        overlay_image_path=overlay_path,
        output_filename=f"reels_{video_info['id']}.mp4"
    )

    print(f"\n🎉 릴스 제작 성공!")
    print(f"📁 완성 파일: {output_path}")
    print(f"==========================================\n")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="해외 유머 릴스 자동 생성기")
    parser.add_argument("--url", type=str, default="https://www.youtube.com/shorts/qC_d_j50nqk", help="변환할 비디오 URL")
    parser.add_argument("--title", type=str, default="외국에서 난리 난 고양이 반응 ㅋㅋㅋ", help="상단 후킹 한글 제목")
    parser.add_argument("--bottom", type=str, default="반응 진짜 킹받네 ㅋㅋㅋ 🤣", help="하단 서브 텍스트")

    args = parser.parse_args()
    create_reels_pipeline(
        video_url=args.url,
        top_title=args.title,
        bottom_text=args.bottom
    )
