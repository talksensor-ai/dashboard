import paramiko

def run_cmd():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    remote_script = """
import json
with open('/Users/ai/talk/pipeline/results_2026-05-21.json') as f:
    data = json.load(f)
print('Total dialogues in results_2026-05-21.json:', len(data.get('results', [])))
for r in data.get('results', []):
    idx = r.get('idx')
    eval_data = r.get('evaluation', {})
    transcript = eval_data.get('transcript', [])
    qa = eval_data.get('qa_evaluation', {})
    print(f"#{idx}:")
    print(f"  Times: {transcript[0]['start'] if transcript else 'N/A'} to {transcript[-1]['end'] if transcript else 'N/A'}")
    print(f"  Loyalty: {qa.get('loyalty_score')}, Upsell: {qa.get('upsell_score')}, Cross-Sales: {qa.get('cross_sales_score')}")
    print(f"  Rec: {qa.get('recommendation')}")
    snippet = "".join([t['text'] for t in transcript[:2]])
    print(f"  Snippet: {snippet[:100]}")
"""
    
    sftp = ssh.open_sftp()
    with sftp.file('/Users/ai/talk/temp_check_details.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('/Users/ai/talk/.venv/bin/python /Users/ai/talk/temp_check_details.py')
    print("--- STDOUT ---")
    print(stdout.read().decode('utf-8'))
    print("--- STDERR ---")
    print(stderr.read().decode('utf-8'))
    
    ssh.exec_command('rm /Users/ai/talk/temp_check_details.py')
    ssh.close()

if __name__ == '__main__':
    run_cmd()
