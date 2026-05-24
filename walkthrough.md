# Walkthrough — Correções, Refatoração, Limpeza, Carga de Fila e Higienização Cadastral (v50.16)

Foram implementadas correções críticas para restabelecer a estabilidade e a integridade da classificação forense de comentários no sistema Sentinela, seguidas por melhorias de compatibilidade Unicode, refatoração de blindagem do supervisor do Watchdog, higienização de arquivos legados, setup da fila de coleta e higienização cadastral de candidatos.

## Alterações Realizadas

### Core & Workers (v50.2)
- **`core/ai_service.py`**:
  - Função `clean_null_chars(data)` que remove caracteres nulos (`\u0000` e `\x00`), prevenindo erros Postgres `22P05`.
  - Elevação do log de classificação forense para `INFO` com o texto decodificado e truncado.
- **`workers/scrapers/ig_zyte.py`** e **`workers/scrapers/ig_headless.py`**:
  - Higienização contra caracteres nulos e cooldown antecipado de alvos (`mark_candidate_scraped`).
- **`workers/base/reward_engine.py`** e **`workers/orchestrator/orchestrator.py`**:
  - Evitar penalizações indevidas de XP por coletas vazias. Suspensão restrita a perdas reais (`delta_xp < 0`).

### Transparência de Recompensas (v50.7)
- **`workers/orchestrator/orchestrator.py`**:
  - Impressão detalhada de `reward.xp_report` (detalhamento por Coleta, Banco, IA, Falhas e Bônus) no console do orquestrador ao final do ciclo.

### Compatibilidade Unicode no Windows (v50.8)
- **`main_runner.py`** e **`watchdog/__init__.py`**:
  - Adicionada reconfiguração de `sys.stdout` e `sys.stderr` no Windows via `sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')`.

### Resiliência a Surrogates UTF-16 de Emojis (v50.9)
- **`core/ai_service.py`**:
  - Atualização da função `safe_decode_unicode` para capturar pares de surrogates adjacentes (ex: `\\ud83c\\udde7`) de forma combinada e realizar a codificação e decodificação UTF-8 com o tratamento de erro `replace`, prevenindo `UnicodeEncodeError: surrogates not allowed`.

### Prevenção de Loops de Erro na Indisponibilidade de IA (v50.10)
- **`core/ai_service.py`**, **`workers/scrapers/ig_zyte.py`** e **`workers/scrapers/ig_headless.py`**:
  - Abortamento imediato dos loops de classificação ao detectar indisponibilidade geral de IA cloud, reduzindo ruído e desperdício de requisições ao banco.

### Refatoração e Blindagem do Watchdog (v50.11)
- **`watchdog/__init__.py`**:
  - Injeção do `PROJECT_ROOT` no `sys.path` antes do carregamento de módulos e suporte ao `load_dotenv()`.
  - Configuração dinâmica de pastas temporárias e cache usando o diretório nativo do SO (`tempfile.gettempdir()`).
  - Segurança das credenciais sensíveis (`CALLMEBOT_PHONE` e `CALLMEBOT_APIKEY`) usando ambiente local.
  - Remoção do taskkill agressivo global sobre `chrome.exe`.

### Higienização do Repositório (v50.12)
- **Limpeza de Backups e Temporários**:
  - Exclusão física e remoção via Git dos arquivos de backup legados de desenvolvimento que poluiam a pasta de scrapers (`workers/scrapers/ig_zyte.py.backup` e `workers/scrapers/ig_zyte.py.backup2`).
  - Remoção de scripts temporários e rascunhos de testes na pasta `scratch/` (`inspect_queue.py`, `test_decode.py` e `test_update_permission.py`).

### Carga de Fila e CSV de Prioridades (v50.13 - v50.14)
- **Operação de Banco e Exportação**:
  - Preenchimento em massa da tabela `fila_coleta` com todos os candidatos ativos do banco remoto Supabase em status `PENDENTE` e prioridade padrão `1`.
  - Geração local do arquivo `prioridade_alvos.csv` na pasta raiz do workspace.
  - Classificação e gravação no banco remoto de todas as prioridades baseadas na matriz de regras fornecida pelo usuário.

### Sincronização e Inserção de Novos Alvos (v50.15)
- **Sincronização Bidirecional**:
  - O script leu o arquivo `prioridade_alvos.csv` alterado pelo operador e identificou **128 novos candidatos** ausentes.
  - Efetuada a inserção automatizada dos 128 novos alvos na tabela `candidatos` do Supabase e o enfileiramento de todos os **467 alvos ativos** na tabela `fila_coleta` com status `"PENDENTE"`.

### Higienização Cadastral de Candidatos (v50.16) [NOVO]
- **Exportação de Dados Faltantes**:
  - Script python temporário desenvolvido para analisar a integridade cadastral de todos os 466 candidatos ativos.
  - Identificados **430 candidatos** que possuem pelo menos um campo de cadastro nulo (`None`) ou vazio (`""`) nas colunas fundamentais: `nome_completo`, `cargo`, `estado`, `partido`, `sexo`, `raca` ou `ideologia`.
  - Gerado o arquivo local `candidatos_dados_faltantes.csv` na raiz do projeto com a listagem detalhada de todos os registros pendentes e uma coluna indicando exatamente quais campos estão vazios (`campos_faltantes`).

### Correção e Resiliência do Frontend em Produção (v50.17) [NOVO]
- **Build Estático e Roteamento Vercel**:
  - Identificada a causa raiz de produção: a Vercel está configurada para pular a compilação do Next.js na nuvem (`echo 'Skip build'`) e servir os arquivos diretamente da raiz do repositório. Por conta disso, as correções anteriores no frontend (pasta `frontend/`) não eram aplicadas.
  - Compilado o Next.js localmente via `npm run build --prefix frontend` gerando os novos estáticos na pasta `frontend/out/`.
  - Removido o build estático legado na raiz e copiados os novos arquivos e pastas (`_next/`, `index.html`, `dashboard.html`, `404.html`, `_not-found.html`) para a raiz.
  - Efetuado o commit e push direto na branch `main` e `feat/autonomous-workers`. O deploy de produção na Vercel foi propagado e a nova versão já está no ar (confirmado via hash de build `DZ8v_bE0UIYhuFuuvcVtF`).
  - As estatísticas (KPIs) no topo, o sensor de pulso temporal das últimas 48h e a listagem em tempo real de alertas ativos agora funcionam de forma 100% resiliente: mesmo que a API serverless falhe (status HTTP != 200), o frontend agora cai automaticamente no fallback que faz requisições diretas ao banco Supabase remoto pelo browser.

### Motor de Coleta & Renovação de Cookies (v52.3) [NOVO]
- **`scripts/export_playwright_cookies.py`**:
  - Implementado suporte robusto a seletores multipropósitos e compatíveis com a acessibilidade (`aria-label`) para lidar com as classes dinâmicas e ofuscadas do Instagram moderno.
  - Tratado o campo de usuário variável (`name="email"` em substituição a `name="username"`).
  - Implementado preenchimento sequencial com atraso simulado de 150ms (`page.type(..., delay=150)`) em vez de inserção instantânea, superando a segurança que bloqueava o botão de ação.
  - Resolvido o login em múltiplas etapas (layouts com senha oculta em primeiro carregamento): emulação de clique em `Enter` e aguardo de transição de 4s para apresentação segura da senha.
  - Validação automatizada e rotação de múltiplos slots `.env` sequenciais (`INSTAGRAM_SESSIONID_X`), atualizando de forma isolada no arquivo `.env` para evitar sobreposição ou falha geral no ciclo.
- **`core/instagram_scraper_v2.py`**:
  - Refatoração total para abertura de posts no feed via modal do Playwright (com clique no elemento) e fechamento por `Escape`, evitando tela branca e bloqueios por acessos diretos a URLs `/p/{shortcode}/`.
- **`core/ai_service.py`**:
  - Integração do modelo de IA local LiteRT (Gemma 3 1B) ao `ai_circuit_breaker`. Em caso de indisponibilidade ou falhas seguidas do modelo local, o circuito abre por 5 minutos, poupando timeouts de 5 segundos repetitivos e mantendo a taxa de processamento do lote alta.

---

## Verificação e Resultados

1. **Renovação de Múltiplos Slots com Sucesso**: Executado o `scripts/export_playwright_cookies.py`, realizando o login automatizado e sem interrupções para duas contas configuradas simultaneamente no `.env`. Os cookies e novos sessionids (`INSTAGRAM_SESSIONID` e `INSTAGRAM_SESSIONID_2`) foram extraídos e injetados de forma estável no `.env` do projeto.
2. **Deploy de Produção Validado**: O site de produção da Vercel (`https://asentinela.vercel.app/`) foi atualizado e está servindo a nova compilação (`DZ8v_bE0UIYhuFuuvcVtF`) livre de caches.
3. **Resiliência do Painel**: O painel carrega com sucesso as estatísticas dinâmicas e o feed de alertas reais do Supabase, contornando a indisponibilidade das rotas de API da Vercel.
4. **Repositório Sincronizado**: O repositório está limpo e os commits foram integrados tanto em `feat/autonomous-workers` quanto em `main`.
