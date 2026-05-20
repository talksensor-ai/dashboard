import os
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

import gigaam
import torch
import tempfile
import soundfile as sf
import numpy as np

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Loading model...")
model = gigaam.load_model('v3_e2e_rnnt', device=device)

# Create a tiny 1-second silent WAV file
sr = 16000
audio_np = np.zeros(sr)
fd, tmp_path = tempfile.mkstemp(suffix=".wav")
sf.write(tmp_path, audio_np, sr)

print("Attempting model.transcribe(tmp_path)...")
try:
    result = model.transcribe(tmp_path)
    print("Success! Result type:", type(result))
    print("Result:", result)
except Exception as e:
    print("Error during transcribe:", e)

print("Attempting model.transcribe(tmp_path, word_timestamps=True)...")
try:
    result = model.transcribe(tmp_path, word_timestamps=True)
    print("Success! Result type:", type(result))
    print("Result:", result)
except Exception as e:
    print("Error during transcribe with word_timestamps:", e)
