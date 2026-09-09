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

def detect_audio_peaks(video_path: str, min_distance_sec: float = 1.2) -> list[dict]:
    """
    원본 오디오의 음량 에너지(RMS) 파형 및 순간 급상승(Onset)을 30ms 단위로 정밀 스캔하여
    타격음, 충격음, 웃음소리, 비명 등 영상의 '중요한 순간'의 정확한 시작 타이밍(초)을 감지합니다.
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

        # 30ms 윈도우 (480 샘플 at 16kHz) 단위 RMS 에너지 및 Onset(기울기) 계산
        window_size = 480
        num_windows = len(data) // window_size
        if num_windows < 10:
            return []

        trimmed_data = data[:num_windows * window_size].reshape((num_windows, window_size))
        rms_values = np.sqrt(np.mean(trimmed_data**2, axis=1))

        mean_rms = float(np.mean(rms_values))
        max_rms = float(np.max(rms_values)) if len(rms_values) > 0 else 1.0
        
        # 에너지 임계치 (평균 대비 1.5배 이상 또는 일정 크기 이상)
        threshold = max(0.06, mean_rms * 1.5)

        peaks = []
        last_t = -999.0
        
        # 순간적으로 소리가 터지는 Onset(상승 엣지) 감지
        for i in range(2, len(rms_values) - 2):
            val = rms_values[i]
            prev_val = rms_values[i - 1]
            diff = val - prev_val
            
            # 음량이 문턱값 이상이고, 급격하게 치솟기 시작한 순간(Attack)
            if val > threshold and diff > 0.02 and val >= rms_values[i + 1]:
                t = round(i * 0.03, 2)
                if t - last_t >= min_distance_sec:
                    peaks.append({"time": t, "energy": float(val), "onset": float(diff)})
                    last_t = t

        # 만약 Onset으로 못 잡은 경우 일반 극대값으로 보강
        if len(peaks) < 2:
            for i in range(1, len(rms_values) - 1):
                val = rms_values[i]
                if val > threshold and val > rms_values[i - 1] and val > rms_values[i + 1]:
                    t = round(i * 0.03, 2)
                    if t - last_t >= min_distance_sec:
                        peaks.append({"time": t, "energy": float(val), "onset": float(val - rms_values[i - 1])})
                        last_t = t

        # 에너지 및 임팩트 순으로 상위 추출 후 시간순 재정렬
        peaks.sort(key=lambda x: x["energy"] * 0.7 + x.get("onset", 0.0) * 0.3, reverse=True)
        top_peaks = sorted(peaks[:7], key=lambda x: x["time"])
        return top_peaks
    except Exception as e:
        print(f"오디오 피크 감지 실패: {e}")
        return []

def analyze_scenes_and_impacts(video_path: str, duration: float) -> list[dict]:
    """
    영상의 실제 씬(클립) 전환점과 각 씬 내부에서
    망치 타격, 손 맞음, 넘어짐, 실수 등 '사건이 터지는 정확한 0.1초 타격 순간(Impact)'을 산출합니다.
    """
    try:
        # 1. FFmpeg Scene Detection (씬 전환점 감지)
        cmd_scenes = [
            'ffmpeg', '-i', video_path,
            '-filter_complex', 'select=\'gt(scene,0.28)\',metadata=print:file=-',
            '-f', 'null', '-'
        ]
        res = subprocess.run(cmd_scenes, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        raw_cuts = [0.0]
        for line in res.stdout.splitlines() + res.stderr.splitlines():
            if 'pts_time:' in line:
                try:
                    t = float(line.split('pts_time:')[1].strip())
                    if t - raw_cuts[-1] >= 1.8 and t < duration - 1.0:
                        raw_cuts.append(round(t, 2))
                except Exception:
                    pass
        if duration not in raw_cuts:
            raw_cuts.append(round(duration, 2))

        # 컷이 너무 없으면 4~6초 단위로 자연스럽게 분할
        if len(raw_cuts) <= 2 and duration >= 8.0:
            step = 5.0
            raw_cuts = [0.0]
            curr = step
            while curr < duration - 1.5:
                raw_cuts.append(round(curr, 2))
                curr += step
            raw_cuts.append(round(duration, 2))

        # 2. 오디오 f32le 덤프로 20ms 단위 정밀 RMS 파형 분석
        raw_audio = str(TEMP_DIR / f"temp_scene_audio_{Path(video_path).stem}.raw")
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', raw_audio
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        data = np.fromfile(raw_audio, dtype=np.float32)
        try:
            os.remove(raw_audio)
        except Exception:
            pass

        win = 320  # 20ms at 16kHz
        num_wins = len(data) // win
        rms_arr = np.sqrt(np.mean(data[:num_wins*win].reshape((num_wins, win))**2, axis=1)) if num_wins > 0 else np.array([])

        clips = []
        for i in range(len(raw_cuts) - 1):
            s = raw_cuts[i]
            e = raw_cuts[i + 1]
            clip_dur = e - s
            if clip_dur < 1.2:
                continue

            # 해당 클립 내의 피크(타격/충격 순간) 탐색
            idx_s = int(s * 50)
            idx_e = min(len(rms_arr), int(e * 50))
            clip_rms = rms_arr[idx_s:idx_e] if len(rms_arr) > 0 else []

            t_impact = None
            if len(clip_rms) > 10:
                # 클립 시작 0.5초 이후의 최대 에너지 지점 탐색
                safe_start_idx = int(min(len(clip_rms) * 0.2, 50 * 0.8))
                sub_rms = clip_rms[safe_start_idx:]
                if len(sub_rms) > 0:
                    sub_max_idx = np.argmax(sub_rms)
                    t_impact = round(s + (safe_start_idx + sub_max_idx) * 0.02, 2)

            # 피크를 못 찾았거나 범위 밖이면 클립의 55% 지점을 타격 순간으로 배정
            if t_impact is None or (t_impact - s < 0.6) or (e - t_impact < 0.35):
                t_impact = round(s + clip_dur * 0.55, 2)

            clips.append({
                'clip_idx': len(clips) + 1,
                'start': s,
                'end': e,
                'impact': t_impact
            })

        print(f"🎬 [클립 정밀 분석 완료] 총 {len(clips)}개 씬 감지 및 타격 순간 도출:", flush=True)
        for c in clips:
            print(f"   - 클립 {c['clip_idx']}: {c['start']:>4.1f}s ~ {c['end']:>4.1f}s | 타격 순간: {c['impact']:>4.2f}s", flush=True)

        return clips
    except Exception as e:
        print(f"씬 및 타격 분석 실패: {e}")
        # 폴백 분할
        return [
            {'clip_idx': 1, 'start': 0.0, 'end': round(duration * 0.5, 2), 'impact': round(duration * 0.25, 2)},
            {'clip_idx': 2, 'start': round(duration * 0.5, 2), 'end': duration, 'impact': round(duration * 0.75, 2)}
        ]

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

