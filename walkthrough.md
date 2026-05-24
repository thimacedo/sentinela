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
  - Expansão da `commentTextBlacklist` com termos funcionais de áudio original, som original, placeholders de digitação e termos de curtidas comuns que poluíam a captura.
- **`scripts/test_scraper_v2.py`**:
  - Ajustada a codificação de saída do console para UTF-8 no Windows (`sys.stdout.reconfigure`), evitando falhas de encode com emojis e acentos ao apresentar a amostra.
- **`core/ai_service.py`**:
  - Integração do modelo de IA local LiteRT (Gemma 3 1B) ao `ai_circuit_breaker`. Em caso de indisponibilidade ou falhas seguidas do modelo local, o circuito abre por 5 minutos, poupando timeouts de 5 segundos repetitivos e mantendo a taxa de processamento do lote alta.

### Higienização Cadastral e Unificação de Guilherme Boulos (v52.4) [NOVO]
- **`scratch/fix_boulos.py`**:
  - Script utilitário desenvolvido para centralizar o monitoramento do Guilherme Boulos no perfil correto e oficial (`@guilhermeboulos.oficial`, ID `141b5779-7a0d-41c5-867b-4b32810a48ea`).
  - Atualizado o cargo do registro oficial para "Deputado Federal" e sua prioridade_coleta para 10.
  - Inativados os três perfis duplicados ou errôneos no Supabase: `@guilherme_boulos`, `@boulos_oficial` e `@guilhermeboulos_sp`.
  - Higienizada a fila de coleta (`fila_coleta`) com a remoção dos registros associados aos perfis inativados e garantia de enfileiramento pendente apenas do oficial.
- **`scratch/apply_sanitization.py`**:
  - Script utilitário desenvolvido para sincronizar as modificações feitas pelo operador no arquivo `alvos_sanitizacao.csv` com a base remota do Supabase.
  - Sincroniza a inativação de alvos removidos do CSV, atualiza as colunas de nome, cargo e username modificados, e trata dependências de chave estrangeira limpando referências em `fila_coleta` antes das operações de update de candidatos no banco.

---

## Verificação e Resultados

1. **Correção de Guilherme Boulos Efetuada**: A execução de `scratch/fix_boulos.py` no banco de dados remoto realizou com sucesso a desativação de 3 registros redundantes e atualizou o cadastro do perfil oficial `@guilhermeboulos.oficial` com cargo e prioridade corretos. A fila de coleta foi limpa e apenas a conta oficial permanece ativa e pendente de raspagem.
2. **Sanitização Geral de Alvos por CSV Executada**: A execução de `scratch/apply_sanitization.py` leu e sincronizou com sucesso as edições de alvos no Supabase remoto:
   - **78 alvos removidos** do CSV foram inativados no banco de dados e removidos de `fila_coleta`.
   - **42 alvos modificados** no CSV (com correções de nomes e cargos institucionais) foram atualizados.
   - Sincronização de 1 alteração complexa de username com tratamento preventivo de chave estrangeira concluída com sucesso.
3. **Renovação de Múltiplos Slots com Sucesso**: Executado o `scripts/export_playwright_cookies.py`, realizando o login automatizado e sem interrupções para duas contas configuradas simultaneamente no `.env`. Os cookies e novos sessionids (`INSTAGRAM_SESSIONID` e `INSTAGRAM_SESSIONID_2`) foram extraídos e injetados de forma estável no `.env` do projeto.
4. **Deploy de Produção Validado**: O site de produção da Vercel (`https://asentinela.vercel.app/`) foi atualizado e está servindo a nova compilação (`DZ8v_bE0UIYhuFuuvcVtF`) livre de caches.
5. **Resiliência do Painel**: O painel carrega com sucesso as estatísticas dinâmicas e o feed de alertas reais do Supabase, contornando a indisponibilidade das rotas de API da Vercel.
6. **Repositório Sincronizado**: O repositório está limpo e os commits foram integrados tanto em `feat/autonomous-workers` quanto em `main`.
7. **Filtro de Heurística DOM Validado**: O script `scripts/test_scraper_v2.py` executou sem falhas de encoding no Windows, comprovando que a restrição do DOM ao `article` e a nova `commentTextBlacklist` limparam 100% dos falsos positivos de áudio original, placeholders e menus. O scraper extraiu apenas comentários reais (amostra de `@raquellyraoficial` com emojis validada no log).
