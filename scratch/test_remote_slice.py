import os
import torchaudio
import tempfile
import sys

target_file = "/Users/ai/talk/2026-05-21_11-56-21-05-2026.ogg"
start_s = 1626
end_s = 1656

print("Loading audio file...")
try:
    waveform, sr = torchaudio.load(target_file)
    print(f"Loaded successfully! SR: {sr}, Shape: {waveform.shape}")
    
    start_idx = int(start_s * sr)
    end_idx = int(end_s * sr)
    
    chunk = waveform[:, start_idx:end_idx]
    
    # Save temporary file
    temp_wav = "/Users/ai/talk/test_slice_1156_1626.wav"
    import soundfile as sf
    sf.write(temp_wav, chunk[0].numpy(), sr)
    print(f"Saved slice to {temp_wav}")
    
    # Use faster-whisper for transcription
    print("Attempting transcription with faster-whisper...")
    from faster_whisper import WhisperModel
    
    # Use cpu for faster load of tiny/base model in testing
    model = WhisperModel("base", device="cpu", compute_type="float32")
    segments, info = model.transcribe(temp_wav, beam_size=5, language="ru")
    
    print("\n--- TRANSCRIPTION RESULT ---")
    for segment in segments:
        print(f"[{segment.start:.1f}s -> {segment.end:.1f}s]: {segment.text}")
    print("----------------------------")
    
except Exception as e:
    print(f"Error: {e}")
