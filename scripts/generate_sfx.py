import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
import wave
import numpy as np
from config import SFX_DIR

def save_wav(filepath: Path, samples: np.ndarray, sample_rate: int = 44100):
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    with wave.open(str(filepath), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(int_samples.tobytes())

def ensure_sfx_assets():
    """
    유튜브 쇼츠 / 틱톡 최상위 예능 및 밈(Meme) 채널에서 필수적으로 쓰이는
    초고타격감 12종 시그니처 효과음 생성:
    - 퍽! (Punch / Hit)
    - 띠용~ (Boing / Spring)
    - 찰싹! (Slap / Smack)
    - 윈도우 에러 (Windows Error)
    - 관객 폭소 (Crowd Laugh)
    - 슉! (Whoosh)
    - 퐁! (Pop)
    - 띵! (Ding)
    - 삐익- (Buzzer)
    - 쿵/폭발 (Boom)
    - 찌익- (Scratch)
    - 지지직 (Glitch)
    """
    SFX_DIR.mkdir(exist_ok=True)
    sr = 44100

    # 1. whoosh.wav (빠른 시선 전환 에어 스윕)
    t = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    noise = np.random.normal(0, 0.7, len(t))
    sweep = np.sin(2 * np.pi * (160 + 1500 * (t / 0.22)**2.2) * t)
    env = (np.sin(np.pi * t / 0.22) ** 2.5) * 1.8
    save_wav(SFX_DIR / 'whoosh.wav', (0.45 * noise + 0.75 * sweep) * env)

    # 2. pop.wav (통통 튀는 퐁! 팝업 효과음)
    t = np.linspace(0, 0.11, int(sr * 0.11), endpoint=False)
    freq = 480 + 1300 * np.exp(-t * 55)
    pop = (np.sin(2 * np.pi * freq * t) * 0.9 + np.sin(2 * np.pi * (freq * 2) * t) * 0.4) * np.exp(-t * 40) * 1.9
    save_wav(SFX_DIR / 'pop.wav', pop)

    # 3. ding.wav (맑고 쨍한 띵!)
    t = np.linspace(0, 0.50, int(sr * 0.50), endpoint=False)
    bell = (np.sin(2 * np.pi * 2349 * t) * 0.7 + np.sin(2 * np.pi * 4698 * t) * 0.4 + np.sin(2 * np.pi * 1174 * t) * 0.25) * np.exp(-t * 7.5) * 1.8
    save_wav(SFX_DIR / 'ding.wav', bell)

    # 4. bonk.wav / punch.wav (묵직한 퍽! 타격음)
    t = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    freq = 650 * np.exp(-t * 32) + 90
    impact_noise = np.random.normal(0, 0.8, len(t)) * np.exp(-t * 60)
    sub_bass = np.sin(2 * np.pi * freq * t) * 1.2
    punch = (sub_bass + impact_noise * 0.7) * np.exp(-t * 22) * 1.9
    save_wav(SFX_DIR / 'bonk.wav', punch)
    save_wav(SFX_DIR / 'punch.wav', punch)

    # 5. boing.wav (만화 띠용~ 반동 스프링)
    t = np.linspace(0, 0.42, int(sr * 0.42), endpoint=False)
    vibrato = np.sin(2 * np.pi * 26 * t) * 170
    base_freq = np.linspace(260, 680, len(t)) + vibrato
    boing = np.sin(np.cumsum(2 * np.pi * base_freq / sr)) * np.exp(-t * 5.5) * 1.8
    save_wav(SFX_DIR / 'boing.wav', boing)

    # 6. slap.wav (찰싹! 뺨/물건 때리는 찰진 손맛 타격음)
    t = np.linspace(0, 0.16, int(sr * 0.16), endpoint=False)
    crack_noise = np.random.normal(0, 1.2, len(t)) * np.exp(-t * 70)
    tonal = np.sin(2 * np.pi * 1200 * np.exp(-t * 40) * t) * 0.7
    slap = (crack_noise + tonal) * np.exp(-t * 30) * 1.9
    save_wav(SFX_DIR / 'slap.wav', slap)

    # 7. windows_error.wav (윈도우 에러 사운드 빰! 황당/뇌정지)
    t = np.linspace(0, 0.35, int(sr * 0.35), endpoint=False)
    chord = (
        np.sin(2 * np.pi * 740 * t) * 0.6 +    # F#5
        np.sin(2 * np.pi * 1108 * t) * 0.5 +   # C#6
        np.sin(2 * np.pi * 1480 * t) * 0.3     # F#6
    ) * np.exp(-t * 8.0) * 1.9
    save_wav(SFX_DIR / 'windows_error.wav', chord)

    # 8. laugh.wav (관객 폭소/웃음소리 하하하!)
    t = np.linspace(0, 0.65, int(sr * 0.65), endpoint=False)
    # 5개의 웃음 펄스 (하-하-하-하-하)
    laugh_pulse = np.zeros_like(t)
    for p_idx, p_time in enumerate([0.02, 0.14, 0.26, 0.38, 0.50]):
        center = int(p_time * sr)
        width = int(0.06 * sr)
        start = max(0, center - width)
        end = min(len(t), center + width)
        w_t = t[start:end] - p_time
        laugh_voice = (np.sin(2 * np.pi * 380 * w_t) * 0.6 + np.sin(2 * np.pi * 760 * w_t) * 0.4)
        laugh_pulse[start:end] += laugh_voice * np.exp(-(w_t * 50)**2) * (1.0 - p_idx * 0.12)
    save_wav(SFX_DIR / 'laugh.wav', laugh_pulse * 1.8)

    # 9. camera.wav (찰칵! 순간포착 셔터)
    t = np.linspace(0, 0.18, int(sr * 0.18), endpoint=False)
    click1 = np.random.normal(0, 0.8, len(t)) * np.exp(-t * 90)
    delay_click2 = int(0.065 * sr)
    click2 = np.zeros_like(t)
    if delay_click2 < len(t):
        t_sub = t[:-delay_click2]
        click2[delay_click2:] = np.random.normal(0, 1.0, len(t_sub)) * np.exp(-t_sub * 80)
    save_wav(SFX_DIR / 'camera.wav', (click1 * 0.8 + click2 * 1.0) * 1.8)

    # 10. buzzer.wav (황당/오답 삐익-)
    t = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
    buzz = (np.sin(2 * np.pi * 180 * t) * 0.6 + np.sin(2 * np.pi * 360 * t) * 0.4 + np.sin(2 * np.pi * 540 * t) * 0.3) * np.exp(-t * 4.5) * 1.8
    save_wav(SFX_DIR / 'buzzer.wav', buzz)

    # 11. boom.wav (쿵! 폭발/대참사)
    t = np.linspace(0, 0.55, int(sr * 0.55), endpoint=False)
    sub = np.sin(2 * np.pi * (140 * np.exp(-t * 8) + 40) * t) * 1.2
    exp_noise = np.random.normal(0, 0.9, len(t)) * np.exp(-t * 12)
    boom = (sub + exp_noise * 0.6) * np.exp(-t * 5.0) * 1.9
    save_wav(SFX_DIR / 'boom.wav', boom)

    # 12. glitch.wav (지지직 멘붕)
    t = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    glitch_noise = np.random.uniform(-1, 1, len(t)) * (np.sin(2 * np.pi * 90 * t) > 0)
    save_wav(SFX_DIR / 'glitch.wav', glitch_noise * np.exp(-t * 8.0) * 1.6)

    # 13. scratch.wav (레코드 찌익-)
    t = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
    scr_freq = 750 + 500 * np.sin(2 * np.pi * 18 * t)
    scr = (np.sin(np.cumsum(2 * np.pi * scr_freq / sr)) * 0.6 + np.random.normal(0, 0.5, len(t)) * 0.4) * np.sin(np.pi * t / 0.28) * 1.9
    save_wav(SFX_DIR / 'scratch.wav', scr)

if __name__ == "__main__":
    ensure_sfx_assets()
    print("모든 예능 밈 효과음 생성 완료!")
