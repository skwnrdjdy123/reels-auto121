import os
import sys
import uuid
import yt_dlp
from config import TEMP_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def download_video(video_url: str, max_duration: int = None) -> dict:
    """
    yt-dlp를 사용하여 주어진 URL(YouTube Shorts, TikTok, Reddit, Instagram 등)의 비디오를 다운로드합니다.
    max_duration이 지정된 경우에만 앞부분 N초를 자르고, 기본값은 쇼츠 전체를 온전히 다운로드합니다.
    """
    unique_id = uuid.uuid4().hex[:8]
    output_template = str(TEMP_DIR / f"raw_{unique_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }

    if max_duration:
        # 비디오 앞부분 max_duration 초만 다운로드 (고속 다운로드 및 테스트)
        ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(0, max_duration)])
        ydl_opts['force_keyframes_at_cuts'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        downloaded_file = str(TEMP_DIR / f"raw_{unique_id}.mp4")

        # 확장자가 mkv 등으로 병합된 경우 mp4 확인
        if not os.path.exists(downloaded_file):
            for ext in ['mp4', 'mkv', 'webm']:
                cand = str(TEMP_DIR / f"raw_{unique_id}.{ext}")
                if os.path.exists(cand):
                    downloaded_file = cand
                    break

        return {
            'file_path': downloaded_file,
            'title': info.get('title', '해외 바이럴 릴스'),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', 'Unknown'),
            'id': unique_id
        }

if __name__ == "__main__":
    test_url = "https://www.youtube.com/shorts/3i_b7X9hY2k" # 테스트용 짧은 쇼츠
    print("다운로드 테스트 시작...")
    try:
        res = download_video(test_url)
        print("성공:", res)
    except Exception as e:
        print("오류:", e)
