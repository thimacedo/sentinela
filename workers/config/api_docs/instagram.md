# Documentação Técnica: Instagram Scraper V2 (PASA v84.3)

## Visão Geral
O motor V2 utiliza Playwright para navegação direta e interceptação de rede. Ele não depende da API oficial, utilizando sessões de usuários reais (cookies).

## Fluxo de Operação
1. **Autenticação**: Utiliza `sessionid` do arquivo `.env`. Se falhar, rotaciona para a próxima sessão.
2. **Navegação**: 
   - Acessa o perfil do candidato diretamente via URL.
   - Abre postagens via navegação direta para `/p/{shortcode}/` (v84.3).
3. **Extração (Tiers de Resiliência)**:
   - **Tier 1 (Interceptação)**: Captura JSONs de `graphql/query` ou `comments` via interceptador de rede.
   - **Tier 2 (Scripts)**: Lê tags `<script type="application/json">` na página.
   - **Tier 3 (DOM)**: Heurística baseada em seletores CSS (`article`, `span[dir="auto"]`).

## Códigos de Erro e Diagnóstico
- `junk_detected`: Ocorreu quando o scraper não encontrou nenhum comentário válido no post. Pode ser causado por:
    - Post sem comentários.
    - Sessão expirada/bloqueada (o conteúdo não carrega).
    - Mudança nos seletores do Instagram (DOM).
- `all_sessions_blocked`: Todas as contas no `.env` foram invalidadas (403, 429 ou Login Wall). Requer intervenção manual para renovação de cookies.
- `login_wall`: O Instagram redirecionou para a página de login. Indica que a sessão foi invalidada.

## Estratégias de Recuperação
- **Cooldown**: Aguardar 6h após detecção de bloqueio massivo.
- **Renovação**: Executar `scripts/export_playwright_cookies.py --force`.
- **Validação**: Verificar `logs/evidence/` para ver screenshots das falhas.
