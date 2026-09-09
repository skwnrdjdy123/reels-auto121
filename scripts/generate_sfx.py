import os
import wave
import numpy as np
from config import SFX_DIR

def save_wav(filename, samples, sample_rate=44100):
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    with wave.open(str(filename), 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(int_samples.tobytes())

def ensure_sfx_assets():
    """
    유튜브 쇼츠 상위 1% 바이럴 채널에서 실제로 쓰이는
    고타격감, 선명한 어택감, 리얼한 음질의 10대 핵심 효과음 생성
    """
    SFX_DIR.mkdir(exist_ok=True)
    sr = 44100

    # 1. whoosh.wav (시선 집중 슉! 빠른 에어 스윕)
    f_whoosh = SFX_DIR / 'whoosh.wav'
    t_w = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
    noise = np.random.normal(0, 0.7, len(t_w))
    sweep = np.sin(2 * np.pi * (180 + 1400 * (t_w / 0.25)**2.2) * t_w)
    env_w = (np.sin(np.pi * t_w / 0.25) ** 2.5) * 1.8
    whoosh = (0.45 * noise + 0.75 * sweep) * env_w
    save_wav(f_whoosh, whoosh)

    # 2. pop.wav (쨍하고 찰진 '퐁!' 버블 어택)
    f_pop = SFX_DIR / 'pop.wav'
    t_p = np.linspace(0, 0.12, int(sr * 0.12), endpoint=False)
    freq_p = 450 + 1200 * np.exp(-t_p * 50)
    harmonics = (
        np.sin(2 * np.pi * freq_p * t_p) * 0.9 +
        np.sin(2 * np.pi * (freq_p * 2) * t_p) * 0.4
    )
    pop = harmonics * np.exp(-t_p * 35) * 1.9
    save_wav(f_pop, pop)

    # 3. ding.wav (성공/정답/감탄 맑고 쨍한 '띵!' 호텔 벨 차임)
    f_ding = SFX_DIR / 'ding.wav'
    t_d = np.linspace(0, 0.55, int(sr * 0.55), endpoint=False)
    bell = (
        np.sin(2 * np.pi * 2349 * t_d) * 0.7 +   # D7
        np.sin(2 * np.pi * 4698 * t_d) * 0.4 +   # D8
        np.sin(2 * np.pi * 1174 * t_d) * 0.25    # D6
    ) * np.exp(-t_d * 7.0) * 1.8
    save_wav(f_ding, bell)

    # 4. bonk.wav (웃긴 퍽! 뿅망치 타격감 극대화)
    f_bonk = SFX_DIR / 'bonk.wav'
    t_k = np.linspace(0, 0.20, int(sr * 0.20), endpoint=False)
    freq_k = 650 * np.exp(-t_k * 30) + 120
    thump = np.sin(2 * np.pi * freq_k * t_k) * 0.95 + np.sin(2 * np.pi * (freq_k * 1.6) * t_k) * 0.4
    bonk = thump * np.exp(-t_k * 25) * 2.0
    save_wav(f_bonk, bonk)

    # 5. boing.wav (만화 띠용~ 반동 용수철)
    f_boing = SFX_DIR / 'boing.wav'
    t_bg = np.linspace(0, 0.40, int(sr * 0.40), endpoint=False)
    vibrato = np.sin(2 * np.pi * 28 * t_bg) * 160
    base_freq = np.linspace(280, 620, len(t_bg)) + vibrato
    phase = np.cumsum(2 * np.pi * base_freq / sr)
    boing = np.sin(phase) * np.exp(-t_bg * 6.0) * 1.8
    save_wav(f_boing, boing)

    # 6. camera.wav (리얼 DSLR 셔터 찰칵!)
    f_cam = SFX_DIR / 'camera.wav'
    t_c = np.linspace(0, 0.18, int(sr * 0.18), endpoint=False)
    click1 = np.random.normal(0, 0.8, len(t_c)) * np.exp(-t_c * 90)
    delay_click2 = int(0.065 * sr)
    click2 = np.zeros_like(t_c)
    if delay_click2 < len(t_c):
        t_sub = t_c[:-delay_click2]
        click2[delay_click2:] = np.random.normal(0, 1.0, len(t_sub)) * np.exp(-t_sub * 80)
    cam = (click1 * 0.8 + click2 * 1.0) * 1.8
    save_wav(f_cam, cam)

    # 7. scratch.wav (레코드 찌익- 반전 멈춤)
    f_scr = SFX_DIR / 'scratch.wav'
    t_s = np.linspace(0, 0.30, int(sr * 0.30), endpoint=False)
    scr_freq = 750 + 500 * np.sin(2 * np.pi * 18 * t_s)
    scr_phase = np.cumsum(2 * np.pi * scr_freq / sr)
    scr_noise = np.random.normal(0, 0.6, len(t_s))
    scratch = (np.sin(scr_phase) * 0.6 + scr_noise * 0.5) * np.sin(np.pi * t_s / 0.30) * 1.9
    save_wav(f_scr, scratch)

    # 8. buzzer.wav (오답/황당/탈락 삐익- 날카로운 톱니파)
    f_buz = SFX_DIR / 'buzzer.wav'
    t_bz = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
    # 톱니파 합성을 통한 리얼 버저음
    buzz = (
        np.sin(2 * np.pi * 180 * t_bz) * 0.6 +
        np.sin(2 * np.pi * 360 * t_bz) * 0.4 +
        np.sin(2 * np.pi * 540 * t_bz) * 0.3 +
        np.sin(2 * np.pi * 720 * t_bz) * 0.2
    ) * np.exp(-t_bz * 4.5) * 1.8
    save_wav(f_buz, buzzer=buzz)

def save_wav(filename, samples, sample_rate=44100, buzzer=None):
    if buzzer is not None:
        samples = buzzer
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    with wave.open(str(filename), 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(int_samples.tobytes())

def ensure_sfx_assets():
    SFX_DIR.mkdir(exist_ok=True)
    sr = 44100

    # 1. whoosh.wav
    t_w = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
    noise = np.random.normal(0, 0.7, len(t_w))
    sweep = np.sin(2 * np.pi * (180 + 1400 * (t_w / 0.25)**2.2) * t_w)
    env_w = (np.sin(np.pi * t_w / 0.25) ** 2.5) * 1.8
    save_wav(SFX_DIR / 'whoosh.wav', (0.45 * noise + 0.75 * sweep) * env_w)

    # 2. pop.wav
    t_p = np.linspace(0, 0.12, int(sr * 0.12), endpoint=False)
    freq_p = 450 + 1200 * np.exp(-t_p * 50)
    pop = (np.sin(2 * np.pi * freq_p * t_p) * 0.9 + np.sin(2 * np.pi * (freq_p * 2) * t_p) * 0.4) * np.exp(-t_p * 35) * 1.9
    save_wav(SFX_DIR / 'pop.wav', pop)

    # 3. ding.wav
    t_d = np.linspace(0, 0.55, int(sr * 0.55), endpoint=False)
    bell = (np.sin(2 * np.pi * 2349 * t_d) * 0.7 + np.sin(2 * np.pi * 4698 * t_d) * 0.4 + np.sin(2 * np.pi * 1174 * t_d) * 0.25) * np.exp(-t_d * 7.0) * 1.8
    save_wav(SFX_DIR / 'ding.wav', bell)

    # 4. bonk.wav
    t_k = np.linspace(0, 0.20, int(sr * 0.20), endpoint=False)
    freq_k = 650 * np.exp(-t_k * 30) + 120
    bonk = (np.sin(2 * np.pi * freq_k * t_k) * 0.95 + np.sin(2 * np.pi * (freq_k * 1.6) * t_k) * 0.4) * np.exp(-t_k * 25) * 2.0
    save_wav(SFX_DIR / 'bonk.wav', bonk)

    # 5. boing.wav
    t_bg = np.linspace(0, 0.40, int(sr * 0.40), endpoint=False)
    vibrato = np.sin(2 * np.pi * 28 * t_bg) * 160
    base_freq = np.linspace(280, 620, len(t_bg)) + vibrato
    boing = np.sin(np.cumsum(2 * np.pi * base_freq / sr)) * np.exp(-t_bg * 6.0) * 1.8
    save_wav(SFX_DIR / 'boing.wav', boing)

    # 6. camera.wav
    t_c = np.linspace(0, 0.18, int(sr * 0.18), endpoint=False)
    click1 = np.random.normal(0, 0.8, len(t_c)) * np.exp(-t_c * 90)
    delay_click2 = int(0.065 * sr)
    click2 = np.zeros_like(t_c)
    if delay_click2 < len(t_c):
        t_sub = t_c[:-delay_click2]
        click2[delay_click2:] = np.random.normal(0, 1.0, len(t_sub)) * np.exp(-t_sub * 80)
    save_wav(SFX_DIR / 'camera.wav', (click1 * 0.8 + click2 * 1.0) * 1.8)

    # 7. scratch.wav
    t_s = np.linspace(0, 0.30, int(sr * 0.30), endpoint=False)
    scr_freq = 750 + 500 * np.sin(2 * np.pi * 18 * t_s)
    scratch = (np.sin(np.cumsum(2 * np.pi * scr_freq / sr)) * 0.6 + np.random.normal(0, 0.6, len(t_s)) * 0.5) * np.sin(np.pi * t_s / 0.30) * 1.9
    save_wav(SFX_DIR / 'scratch.wav', scratch)

    # 8. buzzer.wav
    t_bz = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
    buzz = (np.sin(2 * np.pi * 180 * t_bz) * 0.6 + np.sin(2 * np.pi * 360 * t_bz) * 0.4 + np.sin(2 * np.pi * 540 * t_bz) * 0.3 + np.sin(2 * np.pi * 720 * t_bz) * 0.2) * np.exp(-t_bz * 4.5) * 1.8
    save_wav(SFX_DIR / 'buzzer.wav', buzz)

    # 9. boom.wav (묵직한 초저역 서브베이스 쿵!)
    t_b = np.linspace(0, 0.65, int(sr * 0.65), endpoint=False)
    sub_bass = np.sin(2 * np.pi * (140 * np.exp(-t_b * 8) + 42) * t_b)
    boom = (sub_bass * 0.95 + np.random.normal(0, 0.2, len(t_b))) * np.exp(-t_b * 4.0) * 1.9
    save_wav(SFX_DIR / 'boom.wav', boom)

    # 10. glitch.wav (디지털 찌릿 뇌정지)
    t_g = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    pulse = np.sign(np.sin(2 * np.pi * 950 * t_g)) * (np.random.uniform(0, 1, len(t_g)) > 0.35)
    glitch = (pulse * 0.7 + np.random.normal(0, 0.4, len(t_g))) * np.exp(-t_g * 11) * 1.8
    save_wav(SFX_DIR / 'glitch.wav', glitch)

if __name__ == '__main__':
    ensure_sfx_assets()
    print('All high-punch SFX created.')
