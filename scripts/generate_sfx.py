
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

    # 1. whoosh.wav (시선 집중 슉! 바람 스윕 사운드 - 펀치감 강화)
    f_whoosh = SFX_DIR / 'whoosh.wav'
    t_w = np.linspace(0, 0.3, int(sr * 0.3), endpoint=False)
    noise = np.random.uniform(-0.8, 0.8, len(t_w))
    freq_sweep = np.sin(2 * np.pi * (150 + 900 * (t_w / 0.3)**2) * t_w)
    env_w = (np.sin(np.pi * t_w / 0.3) ** 2) * 1.5
    whoosh = (0.5 * noise + 0.7 * freq_sweep) * env_w
    save_wav(f_whoosh, whoosh)

    # 2. pop.wav (경쾌하고 쨍한 퐁! 버블 팝 사운드 - 고주파 강조)
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
        np.sin(2 * np.pi * 2093 * t_d) * 0.6 +   # C7
        np.sin(2 * np.pi * 4186 * t_d) * 0.35 +  # C8
        np.sin(2 * np.pi * 1046 * t_d) * 0.2     # C6
    ) * np.exp(-t_d * 6.5) * 1.5
    save_wav(f_ding, bell)

    # 4. boom.wav (묵직한 임팩트 쿵! 붐 사운드)
    f_boom = SFX_DIR / 'boom.wav'
    t_b = np.linspace(0, 0.6, int(sr * 0.6), endpoint=False)
    sub_bass = np.sin(2 * np.pi * (120 * np.exp(-t_b * 7) + 40) * t_b)
    boom = (sub_bass * 0.9 + np.random.uniform(-0.15, 0.15, len(t_b))) * np.exp(-t_b * 4.5) * 1.4
    save_wav(f_boom, boom)


if __name__ == '__main__':
    ensure_sfx_assets()
    print('SFX check complete')
