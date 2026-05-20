"""Check torch/torchaudio versions and patch deepfilternet if needed."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# Check versions
check_script = '''
import torch
print("torch:", torch.__version__)
import torchaudio
print("torchaudio:", torchaudio.__version__)

# Check if the old API exists
try:
    from torchaudio.backend.common import AudioMetaData
    print("torchaudio.backend.common.AudioMetaData: EXISTS")
except ImportError:
    print("torchaudio.backend.common.AudioMetaData: MISSING (need to patch df/io.py)")
    
# Check new API
try:
    from torchaudio import AudioMetaData
    print("torchaudio.AudioMetaData: EXISTS (new location)")
except ImportError:
    print("torchaudio.AudioMetaData: MISSING")
    
# Show where df is installed
import df
print("df location:", df.__file__)
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_check_versions.py', 'w') as f:
    f.write(check_script)
sftp.close()

_, out, err = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _check_versions.py 2>&1'
)
time.sleep(15)
print(out.read().decode('utf-8', 'replace'))

ssh.close()
