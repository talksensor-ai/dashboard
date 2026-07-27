import paramiko

host = '100.123.93.21'
user = 'ai'
pw = '1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pw)

sftp = ssh.open_sftp()
remote_file = '/Users/ai/talk/test_slice_1156_1626.wav'
local_file = 'e:/talk/scratch/test_slice_1156_1626.wav'

print("Downloading sliced wav...")
sftp.get(remote_file, local_file)
sftp.close()
ssh.close()
print("Downloaded successfully to scratch/test_slice_1156_1626.wav!")
