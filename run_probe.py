import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', port=22, username='root', password='nIyjYRinAVKAPL23bk6f')

code = """
import librosa
import numpy as np
try:
    y, sr = librosa.load('/root/talk/pipeline/2026-04-22_17-18-22-04-2026.ogg', sr=None)
    print(f"Loaded audio: shape={y.shape}, sr={sr}, duration={len(y)/sr:.2f}s")
    print(f"Max amp: {np.max(np.abs(y)):.4f}, Mean energy: {np.mean(y**2):.6f}")
except Exception as e:
    print("Error loading:", e)
"""

with open(r'e:\talk\probe.py', 'w', encoding='utf-8') as f:
    f.write(code)

sftp = ssh.open_sftp()
sftp.put(r'e:\talk\probe.py', '/root/talk/pipeline/probe.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('cd /root/talk/pipeline && /root/talk/.venv/bin/python3 probe.py')
print(stdout.read().decode())
print("STDERR: ", stderr.read().decode())
