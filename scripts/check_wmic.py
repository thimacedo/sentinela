import os
import subprocess
pid = os.getpid()
cmd = f'wmic process where "processid={pid}" get commandline'
output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
print(f"PID: {pid}")
print(f"CommandLine: {output.strip()}")
