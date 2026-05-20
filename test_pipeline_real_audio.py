import os
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

import sys
sys.path.insert(0, '/Users/ai/talk/pipeline')

import traceback
from audio_audit_pipeline import run_gigaam

audio_path = "/Users/ai/talk/2026-05-10_08-00-10-05-2026.ogg"
print(f"File exists: {os.path.exists(audio_path)}")
print(f"File size: {os.path.getsize(audio_path) if os.path.exists(audio_path) else 'N/A'}")

print("Running run_gigaam on real audio file...")
try:
    # We will modify run_gigaam's try block to show the traceback of the exception inside the loop!
    # Wait, instead of running the whole loop, let's copy the code from run_gigaam and print the traceback here.
    import gigaam
    import torchaudio
    import tempfile
    import soundfile as sf
    import numpy as np
    import torch
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = gigaam.load_model("v3_e2e_rnnt", device=device)
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)
        sr = 16000
    audio_np = waveform[0].numpy()
    
    # Let's take the first chunk
    chunk = audio_np[0:int(24.0 * sr)]
    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(tmp_path, chunk, sr)
    
    try:
        print("Transcribing first chunk...")
        result = model.transcribe(tmp_path, word_timestamps=True)
        print("Success! Result:", result)
    except Exception as chunk_e:
        print("Traceback for transcribe error:")
        traceback.print_exc()
        
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
        
except Exception as e:
    traceback.print_exc()
