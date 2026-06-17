# Gerenciamento de Sessões do Instagram (Sentinela)

O projeto Sentinela necessita de acesso logado no Instagram para efetuar o scraping profundo (API XHR + DOM) evitando os bloqueios iniciais para usuários anônimos.

Ao invés de codificar isso localmente em dezenas de `INSTAGRAM_SESSIONID_X` no `.env` (que se torna insustentável ao escalar), a arquitetura adotou um modelo de **Injection e Rotação de Cookies** mais inteligente e dinâmico, baseado na tabela `session_pool` no Supabase. 

## Como funciona (Sticky Proxy Binding)

O módulo em `core/instagram_scraper_v2.py` deriva um `sticky_proxy_id` usando um hash (SHA256) sobre a label da sessão atual. Isso garante que a mesma sessão **sempre** utilize o mesmo proxy residencial (caso `PROXY_URL_TEMPLATE` possua o coringa `{SESSION_ID}` configurado), evitando a "fragmentação de IP" na rede do Instagram. Se o seu IP mudar a cada request para a mesma sessão logada, o IG marca a conta como "Comprometida" e impõe bloqueio (Challenge Checkpoint).

## Adicionando Sessões em Massa

O sistema aceita um inject em massa. Não é recomendável editar o `.env` do Vercel/Render com mais do que 5 sessões porque excede os limites de environment blocks. 

Para a escala planejada na **Fase 12**, as sessões devem ser inseridas e monitoradas através de um Painel Externo ou sub-agente (como um "Account Manager Agent") através do Supabase. 

### Exemplo de Pipeline (A Ser Consolidado):
1. Ferramentas externas (como navegadores automatizados) logão no IG usando credenciais residenciais.
2. Extraem apenas o cookie `sessionid`.
3. Inserem na tabela `ig_sessions` (ou equivalente que a equipe de banco providencie) marcando a data de expiração e o status de cooldown (em caso de Rate Limit / 429).
4. O `ScrapeAgent` vai abstrair o `_load_sessions` do arquivo `.env` para carregar deste pool do Supabase, roteando de forma distribuída.

## Recuperação Automática

Hoje o `core/autopilot/session_healer.py` (Módulo SRE Autônomo) consegue rotacionar as sessões caso veja muitos erros `403` ou `DOM_CHANGE` na conta, renovando sua flag de bloqueio na base. Certifique-se de prever o tempo de cooldown de pelo menos 1 a 3 horas antes de religar uma sessão bloqueada, caso contrário a conta inteira do IG poderá receber *Shadowban*.