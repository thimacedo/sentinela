import os

state_file = 'c:/Projetos/sentinela/STATE.md'
with open(state_file, 'r', encoding='utf-8') as f:
    content = f.read()

content += """- Corrigido constraint `worker_rewards_tier_check` em `reward_engine.py` rebaixando o tier `platinum` para `gold` garantindo persistencia da gamificacao dos workers sem crash do Orquestrador.
"""

with open(state_file, 'w', encoding='utf-8') as f:
    f.write(content)
