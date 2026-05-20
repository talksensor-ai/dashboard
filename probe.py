
import librosa
import numpy as np
try:
    y, sr = librosa.load('/root/talk/pipeline/2026-04-22_17-18-22-04-2026.ogg', sr=None)
    print(f"Loaded audio: shape={y.shape}, sr={sr}, duration={len(y)/sr:.2f}s")
    print(f"Max amp: {np.max(np.abs(y)):.4f}, Mean energy: {np.mean(y**2):.6f}")
except Exception as e:
    print("Error loading:", e)
