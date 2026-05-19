import subprocess
import os

with open('test_output.log', 'w', encoding='utf-8') as f:
    process = subprocess.run(['python', 'run_worker.py', '--target', 'lulaoficial'], capture_output=True, text=True, encoding='utf-8')
    f.write(process.stdout)
    f.write(process.stderr)
print("Teste concluído. Leia test_output.log")
