import os

gemini_file = 'c:/Projetos/sentinela/GEMINI.md'
with open(gemini_file, 'r', encoding='utf-8') as f:
    content = f.read()

# I will add a rule about the database mappings and Zyte cookie fallback
new_rule = """- **Persistência de Comentários**: A ForeignKey `candidato_id` na tabela `comentarios` mapeia para o `username` do alvo, e NÃO para a UUID do banco.
- **Fallback Browser/Zyte**: Todo worker Zyte DEVE injetar cookies (`requestCookies`) caso seja acionado o fallback DOM (Browser Rendering), usando `_shortcode_to_media_id` para contornar posts sem metadata."""

content = content.replace(
    "- **Banco**: Supabase (RLS ativo, Idempotência via `upsert`).",
    "- **Banco**: Supabase (RLS ativo, Idempotência via `upsert`).\n  " + new_rule
)

with open(gemini_file, 'w', encoding='utf-8') as f:
    f.write(content)
