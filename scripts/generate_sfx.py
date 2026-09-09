
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

    # 1. whoosh.wav
    f_whoosh = SFX_DIR / 'whoosh.wav'
    if not f_whoosh.exists():
        t_w = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
        noise = np.random.uniform(-1, 1, len(t_w))
        freq_sweep = np.sin(2 * np.pi * (200 + 600 * (t_w / 0.25)**2) * t_w)
        env_w = np.sin(np.pi * t_w / 0.25) ** 2
        whoosh = (0.6 * noise + 0.4 * freq_sweep) * env_w
        save_wav(f_whoosh, whoosh)

    # 2. pop.wav
    f_pop = SFX_DIR / 'pop.wav'
    if not f_pop.exists():
        t_p = np.linspace(0, 0.12, int(sr * 0.12), endpoint=False)
        freq_p = 450 + 600 * np.exp(-t_p * 40)
        pop = np.sin(2 * np.pi * freq_p * t_p) * np.exp(-t_p * 35)
        save_wav(f_pop, pop)

    # 3. ding.wav
    f_ding = SFX_DIR / 'ding.wav'
    if not f_ding.exists():
        t_d = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        ding = (np.sin(2 * np.pi * 1760 * t_d) * 0.7 + np.sin(2 * np.pi * 3520 * t_d) * 0.3) * np.exp(-t_d * 8)
        save_wav(f_ding, ding)

    # 4. boom.wav
    f_boom = SFX_DIR / 'boom.wav'
    if not f_boom.exists():
        t_b = np.linspace(0, 0.6, int(sr * 0.6), endpoint=False)
        freq_b = 90 * np.exp(-t_b * 6) + 35
        boom = (np.sin(2 * np.pi * freq_b * t_b) * 0.8 + np.random.uniform(-0.2, 0.2, len(t_b))) * np.exp(-t_b * 5)
        save_wav(f_boom, boom)

if __name__ == '__main__':
    ensure_sfx_assets()
    print('SFX check complete')
