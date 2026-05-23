import os
import re

roadmap_file = 'c:/Projetos/sentinela/ROADMAP.md'
with open(roadmap_file, 'r', encoding='utf-8') as f:
    content = f.read()

new_completed_items = """- [x] IGZyteWorker refatorado: fallback de extração via DOM (Browser Rendering)
- [x] IGZyteWorker: injecao de cookies (`requestCookies`) no browser e parser do DOM/GraphQL (React Hydration)
- [x] Correcao da ForeignKey na persistencia: mapeamento de `candidato_id` para o nome de usuario na tabela `comentarios`"""

content = content.replace(
    "- [x] IGZyteWorker: rotacao sequencial de slots, blacklist login wall, fallback storage_state",
    "- [x] IGZyteWorker: rotacao sequencial de slots, blacklist login wall, fallback storage_state\n" + new_completed_items
)

with open(roadmap_file, 'w', encoding='utf-8') as f:
    f.write(content)

state_file = 'c:/Projetos/sentinela/STATE.md'
with open(state_file, 'r', encoding='utf-8') as f:
    state_content = f.read()

# Add detail to state if missing
if "fallback de Browser Rendering" not in state_content:
    print("Estado não tinha detalhes. (Mas eu já adicionei antes, verificando...)")
