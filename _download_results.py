import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')
sftp = ssh.open_sftp()

# Download GigaAM raw transcript
sftp.get('/root/talk/test_compare/results/gigaam_raw.txt', r'e:\talk\test_compare_gigaam_raw.txt')
print("Downloaded gigaam_raw.txt")

# Download DeepSeek Reasoner output
try:
    sftp.get('/root/talk/test_compare/results/pipeline_a_deepseek_reasoner.txt', r'e:\talk\test_compare_deepseek_reasoner.txt')
    print("Downloaded pipeline_a_deepseek_reasoner.txt")
except:
    print("DeepSeek file not found yet")

# Check Gemma 4 progress
try:
    sftp.get('/root/talk/test_compare/results/pipeline_b_gemma4.txt', r'e:\talk\test_compare_gemma4.txt')
    print("Downloaded pipeline_b_gemma4.txt (Gemma 4 done!)")
except:
    print("Gemma 4 still running...")

sftp.close()
ssh.close()
