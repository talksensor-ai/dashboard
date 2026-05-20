"""A/B test v5: DeepFilterNet + GigaAM on a known working audio file."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

ab_test = '''
import os, sys, time, gc
import torch
import torchaudio
import numpy as np
sys.path.insert(0, '/root/talk/pipeline')

TEST_OGG = "/root/talk/pipeline/08-00-02.ogg"
if not os.path.exists(TEST_OGG):
    print(f"Test file not found: {TEST_OGG}")
    sys.exit(1)

print(f"Test file: {TEST_OGG}")
sz_mb = os.path.getsize(TEST_OGG) / 1024 / 1024
print(f"Size: {sz_mb:.1f} MB")

print()
print("=" * 60)
print("TEST B: DeepFilterNet (chunked) + GigaAM")
print("=" * 60)

from df.enhance import init_df, enhance

print("[B] Loading DeepFilterNet3 model...")
t0 = time.time()
model, df_state, _ = init_df()
target_sr = df_state.sr()  # 48000
print(f"[B] Model loaded in {time.time()-t0:.1f}s, target sr={target_sr}")

# Load audio
print("[B] Loading audio with torchaudio...")
waveform, orig_sr = torchaudio.load(TEST_OGG)
print(f"[B] Original: shape={waveform.shape}, sr={orig_sr}")

# Resample to 48kHz
if orig_sr != target_sr:
    print(f"[B] Resampling {orig_sr} -> {target_sr}...")
    waveform = torchaudio.functional.resample(waveform, orig_sr, target_sr)
    
if waveform.shape[0] > 1:
    waveform = waveform[:1]

total_samples = waveform.shape[1]
total_sec = total_samples / target_sr
print(f"[B] Ready: {total_samples} samples, {total_sec:.1f}s at {target_sr}Hz")

# Take just the first 10 minutes to save time for this test
CHUNK_SEC = 300  # 5 minutes
total_sec_to_process = 600
samples_to_process = min(total_sec_to_process * target_sr, total_samples)
waveform = waveform[:, :samples_to_process]
total_samples = waveform.shape[1]

chunk_samples = CHUNK_SEC * target_sr
overlap_sec = 1  # 1 second overlap for smooth transitions
overlap_samples = overlap_sec * target_sr

print(f"[B] Processing {total_sec_to_process}s in {CHUNK_SEC}s chunks with {overlap_sec}s overlap...")
t0 = time.time()

output_chunks = []
pos = 0
chunk_idx = 0

while pos < total_samples:
    chunk_end = min(pos + chunk_samples, total_samples)
    chunk = waveform[:, pos:chunk_end]
    
    chunk_idx += 1
    chunk_dur = chunk.shape[1] / target_sr
    print(f"  Chunk {chunk_idx}: {pos//target_sr}s-{chunk_end//target_sr}s ({chunk_dur:.0f}s)")
    
    # Enhance this chunk
    enhanced_chunk = enhance(model, df_state, chunk)
    
    if isinstance(enhanced_chunk, np.ndarray):
        enhanced_chunk = torch.from_numpy(enhanced_chunk)
    if enhanced_chunk.dim() == 1:
        enhanced_chunk = enhanced_chunk.unsqueeze(0)
    
    # Skip overlap region from previous chunks (except first)
    if pos > 0 and overlap_samples > 0:
        enhanced_chunk = enhanced_chunk[:, overlap_samples:]
    
    output_chunks.append(enhanced_chunk.cpu())
    
    # Move forward by (chunk - overlap) samples
    pos = chunk_end - overlap_samples if chunk_end < total_samples else total_samples
    
    # Clean GPU memory between chunks
    del chunk
    torch.cuda.empty_cache()

# Concatenate all chunks
enhanced_full = torch.cat(output_chunks, dim=1)
denoise_time = time.time() - t0
print(f"[B] All chunks denoised in {denoise_time:.1f}s, final shape={enhanced_full.shape}")

# Save clean WAV
clean_path = "/root/talk/pipeline/test_AB_clean_known.wav"
torchaudio.save(clean_path, enhanced_full, target_sr)
clean_sz = os.path.getsize(clean_path) / 1024 / 1024
print(f"[B] Clean WAV saved: {clean_sz:.1f} MB")

# Free VRAM before GigaAM
del model, df_state, enhanced_full, output_chunks, waveform
gc.collect()
torch.cuda.empty_cache()
print("[B] DeepFilterNet unloaded, VRAM freed")

# Transcribe clean audio with GigaAM
from audio_audit_pipeline import run_gigaam

print("[B] Transcribing CLEAN audio with GigaAM...")
t0 = time.time()
run_gigaam(clean_path, "/root/talk/pipeline/test_AB_transcript_CLEAN_known.txt")
gigaam_time = time.time() - t0
print(f"[B] GigaAM done in {gigaam_time:.1f}s")

# We don't have a raw transcript for just the first 10 minutes, so let's transcribe the first 10 minutes of raw OGG for comparison.
print("[A] Transcribing RAW audio with GigaAM...")
raw_wav = "/root/talk/pipeline/test_AB_raw_known.wav"
wf_raw, sr_raw = torchaudio.load(TEST_OGG)
# First 10 mins
wf_raw = wf_raw[:, :600*sr_raw]
torchaudio.save(raw_wav, wf_raw, sr_raw)

t0 = time.time()
run_gigaam(raw_wav, "/root/talk/pipeline/test_AB_transcript_RAW_known.txt")
gigaam_raw_time = time.time() - t0
print(f"[A] GigaAM done in {gigaam_raw_time:.1f}s")


# ======= COMPARE =======
print()
print("=" * 60)
print("COMPARISON: RAW vs CLEAN")
print("=" * 60)

raw_lines = []
if os.path.exists("/root/talk/pipeline/test_AB_transcript_RAW_known.txt"):
    with open("/root/talk/pipeline/test_AB_transcript_RAW_known.txt", "r", encoding="utf-8") as f:
        raw_lines = [l.strip() for l in f if l.strip() and l.strip().startswith("[")]

clean_lines = []
ct = "/root/talk/pipeline/test_AB_transcript_CLEAN_known.txt"
if os.path.exists(ct):
    with open(ct, "r", encoding="utf-8") as f:
        clean_lines = [l.strip() for l in f if l.strip() and l.strip().startswith("[")]

print(f"[A] RAW transcript:   {len(raw_lines)} lines")
if raw_lines:
    print("  First 3:")
    for l in raw_lines[:3]:
        print(f"    {l}")

print(f"[B] CLEAN transcript: {len(clean_lines)} lines")
if clean_lines:
    print("  First 3:")
    for l in clean_lines[:3]:
        print(f"    {l}")

raw_words = sum(len(l.split("]")[1].split()) for l in raw_lines if "]" in l)
clean_words = sum(len(l.split("]")[1].split()) for l in clean_lines if "]" in l)

print()
print("=== FINAL SUMMARY ===")
print(f"DeepFilterNet denoise: {denoise_time:.1f}s")
print(f"GigaAM raw:            {gigaam_raw_time:.1f}s")
print(f"GigaAM clean:          {gigaam_time:.1f}s")
print(f"Raw  lines/words:  {len(raw_lines)} / {raw_words}")
print(f"Clean lines/words: {len(clean_lines)} / {clean_words}")
if raw_words > 0:
    diff_pct = ((clean_words - raw_words) / raw_words) * 100
    print(f"Word count diff: {diff_pct:+.1f}%")
'''

print("Uploading A/B test script (chunked)...")
sftp = ssh.open_sftp()
with sftp.file('/root/talk/_ab_test_df_known.py', 'w') as f:
    f.write(ab_test)
sftp.close()
print("Uploaded!")

print("\nRunning A/B test on known file (3-5 min)...\n")
_, out, err = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _ab_test_df_known.py 2>&1'
)

while True:
    line = out.readline()
    if not line:
        break
    print(line.rstrip())

exit_code = out.channel.recv_exit_status()
print(f"\nExit code: {exit_code}")
ssh.close()
print("Done!")
