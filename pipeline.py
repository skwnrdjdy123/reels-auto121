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
from banner_maker import create_top_ranking_header, create_caption_overlay
from video_editor import render_reels
from video_finder import generate_human_scene_captions
from config import TEMP_DIR

def create_reels_pipeline(
    video_url: str,
    line1_text: str = "해외에서 화제 된",
    line2_text: str = "눈길을 사로잡는 순간",
    sub_text: str = "(끝까지 보게 되는 장면)",
    bottom_caption: str = None,
    top_title: str = None,
    bottom_text: str = None,
    **kwargs
) -> str:
    """
    유튜브 랭킹 숏폼 스타일 및 장면별 전환되는 인간미 자막 릴스 제작 파이프라인
    """
    if top_title and not line1_text:
        line1_text = "해외에서 화제 된"
        line2_text = top_title

    print(f"\n==========================================")
    print(f"🎬 인스타 최적화 릴스 제작 시작!")
    print(f"🔗 영상 URL: {video_url}")
    print(f"==========================================")

    # 1. 비디오 다운로드 (최대 30초)
    print("\n[1/3] 비디오 다운로드 중...")
    video_info = download_video(video_url, max_duration=30)
    raw_video_path = video_info['file_path']
    duration = video_info.get('duration') or 20.0
    print(f"✓ 원본 다운로드 완료: {video_info['title']} (길이: {duration}초)")

    # 2. 상단 고정 헤더 배너 생성
    print(f"\n[2/3] 상단 고정 헤더 및 장면별 인간미 자막 생성 중...")
    print(f"   - 1줄: {line1_text}")
    print(f"   - 2줄: {line2_text}")
    print(f"   - 서브: {sub_text}")

    header_overlay_path = create_top_ranking_header(
        line1_text=line1_text,
        line2_text=line2_text,
        sub_text=sub_text
    )

    # 3. 억지웃음 없는 장면별 공감형 자막(3단계) 생성
    scene_captions = generate_human_scene_captions(title=video_info['title'], duration=duration)
    caption_items = []
    for idx, sc in enumerate(scene_captions):
        cap_img_path = str(TEMP_DIR / f"caption_{video_info['id']}_{idx}.png")
        create_caption_overlay(sc['text'], cap_img_path)
        caption_items.append({
            'image_path': cap_img_path,
            'start': sc['start'],
            'end': sc['end'],
            'text': sc['text']
        })
        print(f"   - 장면 {idx+1} ({sc['start']}s ~ {sc['end']}s): \"{sc['text']}\"")

    # 4. FFmpeg 릴스 렌더링
    print("\n[3/3] FFmpeg 다중 장면 자막 릴스 렌더링 중...")
    output_path = render_reels(
        input_video_path=raw_video_path,
        overlay_image_path=header_overlay_path,
        caption_items=caption_items,
        output_filename=f"ranking_reels_{video_info['id']}.mp4"
    )

    print(f"\n🎉 릴스 제작 완료!")
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
