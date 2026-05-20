import paramiko
import time

def setup_venv():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    project_dir = '/Users/ai/talk'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    print("Setting up virtual environment on Mac Mini...")
    
    # Using absolute path to python3.12 from brew
    python_path = "/opt/homebrew/bin/python3.12"
    
    commands = [
        f"cd {project_dir} && {python_path} -m venv .venv",
        f"cd {project_dir} && .venv/bin/pip install --upgrade pip",
        f"cd {project_dir} && .venv/bin/pip install torch torchvision torchaudio",
        f"cd {project_dir} && .venv/bin/pip install faster-whisper paramiko python-dotenv openai supabase httpx pydub librosa soundfile yadisk",
        # Check MPS support
        f"cd {project_dir} && .venv/bin/python -c 'import torch; print(\"PyTorch version:\", torch.__version__); print(\"MPS available:\", torch.backends.mps.is_available())'"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # We need to print output in real-time or at least after each command
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        if out: 
            try:
                print(out)
            except UnicodeEncodeError:
                print(out.encode('ascii', errors='replace').decode('ascii'))
        if err: 
            try:
                print(f"Error: {err}")
            except UnicodeEncodeError:
                print(f"Error: {err.encode('ascii', errors='replace').decode('ascii')}")
        
    ssh.close()
    print("Venv setup complete!")

if __name__ == "__main__":
    setup_venv()
