"""Check transcription output files from A/B test."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# Check both transcript files
check = '''
import os

# Check clean transcript
clean = "/root/talk/pipeline/test_AB_transcript_CLEAN.txt"
if os.path.exists(clean):
    with open(clean, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.strip().split("\\n")
    print(f"=== CLEAN transcript ({len(lines)} lines, {len(content)} bytes) ===")
    for l in lines[:20]:
        print(f"  {l}")
    if len(lines) > 20:
        print(f"  ... ({len(lines)-20} more lines)")
else:
    print("CLEAN transcript not found!")

print()

# Check raw transcript  
raw = "/root/talk/pipeline/2026-04-22_17-18-22-04-2026_transcript.txt"
if os.path.exists(raw):
    with open(raw, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.strip().split("\\n")
    print(f"=== RAW transcript ({len(lines)} lines, {len(content)} bytes) ===")
    for l in lines[:20]:
        print(f"  {l}")
    if len(lines) > 20:
        print(f"  ... ({len(lines)-20} more lines)")
else:
    print("RAW transcript not found!")
    
# Check WAV file info
import torchaudio
wav = "/root/talk/pipeline/test_AB_clean.wav"
if os.path.exists(wav):
    waveform, sr = torchaudio.load(wav, num_frames=16000)
    print(f"\\n=== Clean WAV info ===")
    print(f"  Sample rate: {sr}")
    print(f"  File size: {os.path.getsize(wav)/1024/1024:.1f} MB")
    print(f"  RMS of first second: {waveform.abs().mean():.6f}")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_check_transcripts.py', 'w') as f:
    f.write(check)
sftp.close()

_, out, err = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _check_transcripts.py 2>&1'
)
time.sleep(15)
print(out.read().decode('utf-8', 'replace'))
ssh.close()
