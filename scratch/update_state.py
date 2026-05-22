import os
import re

state_file = 'c:/Projetos/sentinela/STATE.md'
with open(state_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Update status
content = content.replace('**Status:** 🔴 Implementação de Workers (Instagram) / Testes', '**Status:** 🟢 Refatoração Concluída / Testes Validados')

content += """
## Ultimas Atualizacoes (Refatoracao Raspagem e Classificacao)
- Corrigidos wrappers de modulos: `InstagramWorker` agindo como proxy para `IGZyteWorker`.
- Adicionada injecao de cookies (`requestCookies`) no `IGZyteWorker` permitindo fallback de Browser Rendering via Zyte com sessoes autenticadas.
- Resolvido conversao de shortcode para `media_id` para lidar com DOM scraping.
- Corrigida referencia da ForeignKey na tabela `comentarios`, usando `candidato_id` mapeado para o `username` do alvo.
- Teste completo end-to-end rodando com sucesso no alvo `lulaoficial`, incluindo extracao, persistencia e classificacao por IA (fallback Mistral ativado devido a limite Groq).
"""

with open(state_file, 'w', encoding='utf-8') as f:
    f.write(content)
