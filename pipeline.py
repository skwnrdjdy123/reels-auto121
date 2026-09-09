import os
import sys
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from downloader import download_video
from banner_maker import create_top_ranking_header, create_bottom_caption
from video_editor import render_reels

def create_reels_pipeline(
    video_url: str,
    line1_text: str = "역대급 해외 바이럴",
    line2_text: str = "웃긴 모먼트 TOP5",
    sub_text: str = "(다들 몇 번이 제일 웃김? ㅋㅋㅋ)",
    bottom_caption: str = "아니 이건 진짜 레전드네 ㅋㅋㅋ 🤣",
    top_title: str = None,
    bottom_text: str = None,
    **kwargs
) -> str:
    """
    유튜브 랭킹 숏폼 스타일(상단 핑크+화이트 볼드 헤더 + 괄호 유도 + 하단 블랙박스 자막) 릴스 제작 파이프라인
    """
    # top_title이 넘어온 경우 처리
    if top_title and not line1_text:
        line1_text = "역대급 해외 바이럴"
        line2_text = top_title
    if bottom_text and not bottom_caption:
        bottom_caption = bottom_text
    """
    유튜브 랭킹 숏폼 스타일(상단 핑크+화이트 볼드 헤더 + 괄호 유도 + 하단 블랙박스 자막) 릴스 제작 파이프라인
    """
    print(f"\n==========================================")
    print(f"🎬 랭킹 스타일 릴스 제작 시작!")
    print(f"🔗 영상 URL: {video_url}")
    print(f"==========================================")

    # 1. 비디오 다운로드 (최대 30초)
    print("\n[1/3] 비디오 다운로드 중...")
    video_info = download_video(video_url, max_duration=30)
    raw_video_path = video_info['file_path']
    print(f"✓ 원본 다운로드 완료: {video_info['title']}")

    # 2. 텍스트 배너 이미지 생성
    print(f"\n[2/3] 상단 고정 헤더 및 자막 생성 중...")
    print(f"   - 1줄: {line1_text}")
    print(f"   - 2줄: {line2_text}")
    print(f"   - 서브: {sub_text}")
    print(f"   - 자막: {bottom_caption}")

    overlay_path = create_top_ranking_header(
        line1_text=line1_text,
        line2_text=line2_text,
        sub_text=sub_text
    )
    if bottom_caption:
        create_bottom_caption(bottom_caption, overlay_path)

    # 3. FFmpeg 릴스 렌더링
    print("\n[3/3] FFmpeg 랭킹 레이아웃 렌더링 중...")
    output_path = render_reels(
        input_video_path=raw_video_path,
        overlay_image_path=overlay_path,
        output_filename=f"ranking_reels_{video_info['id']}.mp4"
    )

    print(f"\n🎉 랭킹 릴스 제작 완료!")
    print(f"📁 완성 파일: {output_path}")
    print(f"==========================================\n")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="랭킹 스타일 릴스 생성기")
    parser.add_argument("--url", type=str, default="https://www.youtube.com/shorts/qC_d_j50nqk")
    parser.add_argument("--line1", type=str, default="역대급 웃긴 고양이")
    parser.add_argument("--line2", type=str, default="모먼트 랭킹 TOP5")
    parser.add_argument("--sub", type=str, default="(다들 몇 번이 제일 웃김? ㅋㅋㅋ)")
    parser.add_argument("--caption", type=str, default="야@무지게 물어버리네;; ㅋㅋㅋ")

    args = parser.parse_args()
    create_reels_pipeline(
        video_url=args.url,
        line1_text=args.line1,
        line2_text=args.line2,
        sub_text=args.sub,
        bottom_caption=args.caption
    )
