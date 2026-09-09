
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
    SFX_DIR.mkdir(exist_ok=True)
    sr = 44100

    # 1. whoosh.wav (시선 집중 슉! 바람 스윕 사운드)
    f_whoosh = SFX_DIR / 'whoosh.wav'
    t_w = np.linspace(0, 0.3, int(sr * 0.3), endpoint=False)
    noise = np.random.uniform(-0.8, 0.8, len(t_w))
    freq_sweep = np.sin(2 * np.pi * (150 + 900 * (t_w / 0.3)**2) * t_w)
    env_w = (np.sin(np.pi * t_w / 0.3) ** 2) * 1.5
    whoosh = (0.5 * noise + 0.7 * freq_sweep) * env_w
    save_wav(f_whoosh, whoosh)

    # 2. pop.wav (경쾌하고 쨍한 퐁! 버블 팝 사운드)
    f_pop = SFX_DIR / 'pop.wav'
    t_p = np.linspace(0, 0.15, int(sr * 0.15), endpoint=False)
    freq_p = 350 + 850 * np.exp(-t_p * 35)
    harmonics = np.sin(2 * np.pi * freq_p * t_p) * 0.8 + np.sin(2 * np.pi * (freq_p * 2) * t_p) * 0.3
    pop = harmonics * np.exp(-t_p * 28) * 1.6
    save_wav(f_pop, pop)

    # 3. ding.wav (맑고 선명하게 울리는 띵! 차임벨 사운드)
    f_ding = SFX_DIR / 'ding.wav'
    t_d = np.linspace(0, 0.6, int(sr * 0.6), endpoint=False)
    bell = (
        np.sin(2 * np.pi * 2093 * t_d) * 0.6 +
        np.sin(2 * np.pi * 4186 * t_d) * 0.35 +
        np.sin(2 * np.pi * 1046 * t_d) * 0.2
    ) * np.exp(-t_d * 6.5) * 1.5
    save_wav(f_ding, bell)

    # 4. bonk.wav (웃긴 퍽! 뿅망치 타격 사운드)
    f_bonk = SFX_DIR / 'bonk.wav'
    t_k = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    freq_k = 480 * np.exp(-t_k * 25) + 80
    bonk = (np.sin(2 * np.pi * freq_k * t_k) * 0.85 + np.sin(2 * np.pi * (freq_k * 1.5) * t_k) * 0.3) * np.exp(-t_k * 22) * 1.7
    save_wav(f_bonk, bonk)

    # 5. boing.wav (만화 띠용~ 스프링 반동 사운드)
    f_boing = SFX_DIR / 'boing.wav'
    t_bg = np.linspace(0, 0.45, int(sr * 0.45), endpoint=False)
    lfo = np.sin(2 * np.pi * 22 * t_bg) * 120
    freq_bg = np.linspace(260, 520, len(t_bg)) + lfo
    phase = np.cumsum(2 * np.pi * freq_bg / sr)
    boing = np.sin(phase) * np.exp(-t_bg * 5.5) * 1.5
    save_wav(f_boing, boing)

    # 6. camera.wav (순간포착 찰칵! 셔터 사운드)
    f_cam = SFX_DIR / 'camera.wav'
    t_c = np.linspace(0, 0.2, int(sr * 0.2), endpoint=False)
    click1 = np.random.uniform(-1, 1, len(t_c)) * np.exp(-t_c * 80)
    delay_click2 = int(0.08 * sr)
    click2 = np.zeros_like(t_c)
    if delay_click2 < len(t_c):
        t_sub = t_c[:-delay_click2]
        click2[delay_click2:] = np.random.uniform(-1, 1, len(t_sub)) * np.exp(-t_sub * 70)
    cam = (click1 * 0.7 + click2 * 0.9) * 1.5
    save_wav(f_cam, cam)

    # 7. scratch.wav (분위기 반전 레코드 스크래치 찌익-)
    f_scr = SFX_DIR / 'scratch.wav'
    t_s = np.linspace(0, 0.35, int(sr * 0.35), endpoint=False)
    scr_freq = 600 + 400 * np.sin(2 * np.pi * 14 * t_s)
    scr_phase = np.cumsum(2 * np.pi * scr_freq / sr)
    scr_noise = np.random.uniform(-0.6, 0.6, len(t_s))
    scratch = (np.sin(scr_phase) * 0.5 + scr_noise * 0.5) * np.sin(np.pi * t_s / 0.35) * 1.6
    save_wav(f_scr, scratch)

    # 8. buzzer.wav (오답/황당 삐익- 전자음 사운드)
    f_buz = SFX_DIR / 'buzzer.wav'
    t_bz = np.linspace(0, 0.3, int(sr * 0.3), endpoint=False)
    buzzer = (np.sign(np.sin(2 * np.pi * 160 * t_bz)) * 0.5 + np.sin(2 * np.pi * 320 * t_bz) * 0.4) * np.exp(-t_bz * 4) * 1.4
    save_wav(f_buz, buzzer)

    # 9. boom.wav (묵직한 임팩트 쿵! 붐 사운드)
    f_boom = SFX_DIR / 'boom.wav'
    t_b = np.linspace(0, 0.6, int(sr * 0.6), endpoint=False)
    sub_bass = np.sin(2 * np.pi * (120 * np.exp(-t_b * 7) + 40) * t_b)
    boom = (sub_bass * 0.9 + np.random.uniform(-0.15, 0.15, len(t_b))) * np.exp(-t_b * 4.5) * 1.5
    save_wav(f_boom, boom)

    # 10. glitch.wav (디지털 찌릿 지지직 사운드)
    f_gli = SFX_DIR / 'glitch.wav'
    t_g = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
    pulse = np.sign(np.sin(2 * np.pi * 800 * t_g)) * (np.random.uniform(0, 1, len(t_g)) > 0.4)
    glitch = (pulse * 0.6 + np.random.uniform(-0.4, 0.4, len(t_g))) * np.exp(-t_g * 12) * 1.5
    save_wav(f_gli, glitch)



if __name__ == '__main__':
    ensure_sfx_assets()
    print('SFX check complete')
