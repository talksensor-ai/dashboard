"""
Patch vad_utils.py: set onset/offset DIRECTLY on pipeline object (not through instantiate).
For segmentation-3.0 powerset model, onset/offset are fixed attrs, not tunable params.
"""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

vad_path = '/root/GigaAM/gigaam/vad_utils.py'

# Step 1: First revert the broken patch (put back original instantiate line)
# Then add onset/offset assignment AFTER instantiate
patch_script = '''
path = "/root/GigaAM/gigaam/vad_utils.py"
with open(path, "r") as f:
    content = f.read()

# Fix: replace the broken patched line back to original, then add onset/offset lines
old_broken = '    _PIPELINE.instantiate({"onset": 0.3, "offset": 0.3, "min_duration_on": 0.0, "min_duration_off": 0.5})'
original = '    _PIPELINE.instantiate({"min_duration_on": 0.0, "min_duration_off": 0.0})'

if old_broken in content:
    content = content.replace(old_broken, original)
    print("Reverted broken patch to original instantiate line")

# Now add onset/offset override AFTER instantiate (if not already there)
if "# VAD sensitivity patch" not in content:
    new_lines = original + """
    # VAD sensitivity patch: lower thresholds for noisy coffee shop audio
    _PIPELINE.onset = 0.35
    _PIPELINE.offset = 0.35"""
    content = content.replace(original, new_lines)
    print("Added onset/offset override after instantiate")
else:
    print("Patch already applied")

with open(path, "w") as f:
    f.write(content)

print("\\nVerification - lines around instantiate:")
with open(path, "r") as f:
    for i, line in enumerate(f, 1):
        if 73 <= i <= 82:
            print(f"  {i}: {line.rstrip()}")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_patch_vad2.py', 'w') as f:
    f.write(patch_script)
sftp.close()

_, o, e = c.exec_command('python3 /root/talk/_patch_vad2.py', timeout=30)
print(o.read().decode())
err = e.read().decode().strip()
if err:
    print(f'STDERR: {err}')

# Step 2: Verify the patch works by loading the pipeline
print("\n=== Testing patched pipeline ===")
test_script = '''
import sys
sys.path.insert(0, "/root/GigaAM")
import gigaam.vad_utils as vu
vu._PIPELINE = None  # force reload

from gigaam.vad_utils import get_pipeline
import torch
pipeline = get_pipeline(torch.device("cuda"))
print(f"onset = {pipeline.onset}")
print(f"offset = {pipeline.offset}")
print(f"min_duration_on = {pipeline.min_duration_on}")
print(f"min_duration_off = {pipeline.min_duration_off}")

if pipeline.onset < 0.5:
    print("\\nSUCCESS: VAD sensitivity increased!")
else:
    print("\\nFAILED: onset still at default")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_test_patch.py', 'w') as f:
    f.write(test_script)
sftp.close()

_, o, e = c.exec_command('/root/talk/.venv/bin/python3 /root/talk/_test_patch.py', timeout=60)
print(o.read().decode())
err = e.read().decode().strip()
if err:
    print(f'STDERR: {err}')

c.close()
print("Done!")
