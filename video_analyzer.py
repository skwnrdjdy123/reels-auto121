import os
import sys
import json
import subprocess
import numpy as np
from pathlib import Path
from config import TEMP_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def detect_video_cuts(video_path: str) -> list[float]:
    """
    영상 내 실제 장면 전환(I-프레임 컷) 타임스탬프(초)를 정밀 감지합니다.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_frames", "-show_entries", "frame=pts_time,pict_type",
            "-select_streams", "v", "-of", "json",
            video_path
        ]
        res = subprocess.check_output(cmd, text=True, errors="replace")
        frames = json.loads(res).get("frames", [])
        cuts = []
        for f in frames:
            if f.get("pict_type") == "I":
                t = float(f.get("pts_time", 0.0))
                # 너무 가까운 컷(1.0초 미만)은 병합
                if not cuts or (t - cuts[-1] >= 1.2):
                    cuts.append(round(t, 2))
        if 0.0 not in cuts:
            cuts.insert(0, 0.0)
        return cuts
    except Exception as e:
        print(f"장면 전환 감지 실패: {e}")
        return [0.0]

def detect_audio_peaks(video_path: str, min_distance_sec: float = 1.5) -> list[dict]:
    """
    원본 오디오의 음량 에너지(RMS) 파형을 50ms 단위로 정밀 스캔하여
    웃음 터지는 순간, 타격음, 고함, 쿵 소리 등 핵심 하이라이트 타이밍(초)을 감지합니다.
    """
    try:
        raw_audio_path = str(TEMP_DIR / f"temp_rms_{Path(video_path).stem}.raw")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-f", "f32le", raw_audio_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        data = np.fromfile(raw_audio_path, dtype=np.float32)
        try:
            os.remove(raw_audio_path)
        except Exception:
            pass

        if len(data) == 0:
            return []

        # 50ms 윈도우 (800 샘플) 단위 RMS 에너지 계산
        window_size = 800
        num_windows = len(data) // window_size
        if num_windows == 0:
            return []

        trimmed_data = data[:num_windows * window_size].reshape((num_windows, window_size))
        rms_values = np.sqrt(np.mean(trimmed_data**2, axis=1))

        mean_rms = np.mean(rms_values)
        threshold = max(0.08, mean_rms * 1.6)

        peaks = []
        last_t = -999.0
        for i in range(1, len(rms_values) - 1):
            val = rms_values[i]
            if val > threshold and val > rms_values[i - 1] and val > rms_values[i + 1]:
                t = round(i * 0.05, 2)
                if t - last_t >= min_distance_sec:
                    peaks.append({"time": t, "energy": float(val)})
                    last_t = t

        # 에너지 순서로 상위 정렬 후 시간순 재정렬
        peaks.sort(key=lambda x: x["energy"], reverse=True)
        top_peaks = sorted(peaks[:8], key=lambda x: x["time"])
        return top_peaks
    except Exception as e:
        print(f"오디오 피크 감지 실패: {e}")
        return []

def analyze_video_highlights(video_path: str, duration: float) -> dict:
    """
    영상 컷과 오디오 피크를 종합 분석하여
    자막 전환 포인트 및 효과음이 정확히 꽂혀야 할 황금 타이밍을 산출합니다.
    """
    cuts = detect_video_cuts(video_path)
    peaks = detect_audio_peaks(video_path)

    peak_times = [p["time"] for p in peaks]
    print(f"🎯 [비디오 AI 분석] 감지된 장면 전환(컷): {cuts}", flush=True)
    print(f"🔊 [오디오 AI 분석] 감지된 하이라이트 피크: {peak_times}", flush=True)

    return {
        "cuts": cuts,
        "peaks": peak_times,
        "duration": duration
    }
