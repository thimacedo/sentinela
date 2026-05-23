# Walkthrough — Correções, Refatoração, Limpeza e Carga de Fila de Coleta (v50.13)

Foram implementadas correções críticas para restabelecer a estabilidade e a integridade da classificação forense de comentários no sistema Sentinela, seguidas por melhorias de compatibilidade Unicode, refatoração de blindagem do supervisor do Watchdog, higienização de arquivos legados e o setup manual da fila de coleta.

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

### Carga de Fila e CSV de Prioridades (v50.13)
- **Operação de Banco e Exportação**:
  - Preenchimento em massa da tabela `fila_coleta` com todos os **338 candidatos ativos** do banco remoto Supabase em status `PENDENTE` e prioridade padrão `1`.
  - Geração local do arquivo `prioridade_alvos.csv` na pasta raiz do workspace. O arquivo contém as colunas `candidato_id`, `nome` (nome completo mapeado da coluna `nome_completo` do banco), `partido`, `prioridade` (padrão `1`) e `status` (padrão `PENDENTE`).
  - O operador poderá abrir o CSV diretamente no Excel ou editor de planilha, redefinir a prioridade numérica de cada alvo e devolvê-lo para importação direta no banco.

---

## Verificação e Resultados

1. **Setup de Fila Concluído**: Todos os 338 candidatos ativos já estão cadastrados na fila remota. O orquestrador priorizará essa fila no próximo ciclo.
2. **Arquivo CSV Gerado**: O arquivo local `prioridade_alvos.csv` de 16 KB foi salvo com sucesso na raiz do projeto.
3. **Repositório Higienizado**: A árvore de trabalho do Git está completamente limpa (`nothing to commit, working tree clean`).
