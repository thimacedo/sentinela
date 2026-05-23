import os
import sys
import json
import re

log_file = r'C:\Users\THIAGO\.gemini\antigravity-ide\brain\d2e3d996-d9bb-4710-8681-33bd51e58a08\.system_generated\tasks\task-693.log'

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

results = []
for line in lines:
    if '[orchestrator]' in line and 'ciclo #' in line and '| target=' in line:
        match = re.search(r'target=([\w\.\-]+) \| origem=(\w+) \| extraidos=(\d+) \| inseridos=(\d+) \| duplicados=(\d+) \| classificados=(\d+).*?score=([\d\.]+)', line)
        if match:
            target, origem, ext, ins, dup, classif, score = match.groups()
            results.append({
                'target': target,
                'origem': origem,
                'ext': int(ext),
                'ins': int(ins),
                'dup': int(dup),
                'classif': int(classif),
                'score': float(score)
            })

print(f"Total de ciclos concluidos: {len(results)}")
for r in results:
    print(f"Alvo: @{r['target']:<20} | Origem: {r['origem']:<8} | Ext: {r['ext']:<3} | Ins: {r['ins']:<3} | Dup: {r['dup']:<3} | IA: {r['classif']:<3} | Score: {r['score']}")
