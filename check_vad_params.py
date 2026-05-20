"""Check exactly how onset/offset are exposed in VAD pipeline for powerset models."""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

script = '''
import sys, inspect
sys.path.insert(0, "/root/GigaAM")
from pyannote.audio.pipelines import VoiceActivityDetection
from gigaam.vad_utils import load_segmentation_model

model = load_segmentation_model("pyannote/segmentation-3.0")

# Check the __init__ source to see how onset/offset are created
print("=== VoiceActivityDetection.__init__ source ===")
src = inspect.getsource(VoiceActivityDetection.__init__)
print(src)

print("\\n=== VoiceActivityDetection.initialize source ===")
try:
    src = inspect.getsource(VoiceActivityDetection.initialize)
    print(src)
except:
    print("No initialize method")

# Try creating pipeline and see what happens with powerset model
pipeline = VoiceActivityDetection(segmentation=model)

# Check if onset exists as attribute
print(f"\\nHas onset attr: {hasattr(pipeline, 'onset')}")
print(f"onset value: {pipeline.onset if hasattr(pipeline, 'onset') else 'N/A'}")
print(f"offset value: {pipeline.offset if hasattr(pipeline, 'offset') else 'N/A'}")

# Check all attributes
print("\\nAll pipeline attributes with values:")
for attr in sorted(dir(pipeline)):
    if not attr.startswith("_"):
        try:
            val = getattr(pipeline, attr)
            if not callable(val):
                print(f"  {attr} = {val}")
        except:
            pass

# List ALL parameters including non-instantiated
print("\\nAll parameters (raw):")
for name, param in pipeline.parameters().items():
    print(f"  {name}: type={type(param).__name__}, value={param}")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_check_onset.py', 'w') as f:
    f.write(script)
sftp.close()

_, o, e = c.exec_command('/root/talk/.venv/bin/python3 /root/talk/_check_onset.py', timeout=60)
print(o.read().decode())
err = e.read().decode().strip()
if err:
    print(f'STDERR:\n{err}')
c.close()
