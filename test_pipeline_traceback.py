import os
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

import sys
sys.path.insert(0, '/Users/ai/talk/pipeline')

import traceback
from audio_audit_pipeline import run_gigaam
import tempfile
import soundfile as sf
import numpy as np

# Create a tiny 5-second dummy audio
sr = 16000
audio_np = np.random.randn(sr * 5) * 0.01
fd, tmp_path = tempfile.mkstemp(suffix=".wav")
sf.write(tmp_path, audio_np, sr)

print("Running run_gigaam on dummy audio...")
try:
    # We will modify run_gigaam temporarily or just run it to see if it prints traceback
    # Let's run it.
    run_gigaam(tmp_path, "dummy_out.txt")
except Exception as e:
    print("Caught error in outer block:")
    traceback.print_exc()

if os.path.exists(tmp_path):
    os.remove(tmp_path)
