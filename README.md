# Sentinela

Plataforma de monitoramento e inteligência política com coleta automatizada, classificação assistida por IA, mineração de rede, geração de dossiês e supervisão operacional via Watchdog.

## Estado atual

- Backend principal: `main_runner.py`
- Supervisão local: `watchdog/__init__.py`
- Frontend oficial: `frontend/`
- Dashboard local de operação: `local_dashboard.html`
- Fonte de verdade operacional: `STATE.md`
- Direção de produto/execução: `ROADMAP.md`

## Arquitetura real em produção

O fluxo atual observado no código é:

1. `watchdog` inicia e supervisiona `main_runner.py`
2. o orquestrador registra workers especializados
3. a fila usa claim atômico com `SELECT FOR UPDATE SKIP LOCKED` via RPCs do Supabase
4. o scraper coleta comentários e metadados
5. `WkClassificaComentarios` classifica backlog com cascata:
   - `ollama` para triagem local
   - `maritaca` (Sabia-4) e `huggingface` (MCP) na camada cloud
   - `mistral`, `groq` e `openrouter` como provedores de auditoria
   - `FallbackLLM` como recuperação de desastre
6. `sa-mineracao-redes` consolida redes e clusters de ataque
7. `sa-auditoria-financeira` atualiza indicadores financeiros e DRE
8. `sa-fast-drop` realiza triagem léxica local sem JVM de forma ultra-veloz

## Estado atual dos workers

Workers ativos no runtime moderno:

- `workers/scrapers/wk_coleta_instagram.py` (`WkColetaInstagram`) — coleta Instagram com fila atômica, diagnóstico granular de coleta zero e extrator multi-camada (API interna + DOM Healing + fallback DOM)
- `workers/processors/wk_classifica_comentarios.py` (`WkClassificaComentarios`) — classificador oficial e reanálise de baixa confiança
- `workers/analytics/sa_mineracao_redes.py` (`SaMineracaoRedes`) — mineração de rede e clusters reativos
- `workers/financial/sa_auditoria_financeira.py` (`SaAuditoriaFinanceira`) — auditoria e telemetria financeira
- `workers/processors/wk_pesquisa_alvos.py` (`WkPesquisaAlvos`) — curadoria de alvos, controlado por modo explícito
- `workers/ai/sa_fast_drop.py` (`SaFastDrop`) — triagem fast-drop local léxica sem dependências externas
- `workers/orchestrator/orchestrator.py` — coordenação e autocura reativa do runtime moderno

Refatorações já concluídas nesta frente:

- expurgo dos entrypoints e contratos legados que competiam com o runtime oficial
- absorção da lógica útil de padrão ouro do antigo `ClassifierWorker` para `core/ai_service.py`
- desativação padrão do `researcher-01` com `RESEARCHER_MODE=disabled`
- atualização dos scripts auxiliares para apontar para `main_runner.py` e `scripts/run_scanner_agent.py`

## Entrada oficial

```bash
python main_runner.py
```

## Supervisão operacional

```bash
python -m watchdog
```

ou pelos atalhos/scripts locais já existentes no workspace.

## Frontend oficial

O frontend oficial está em `frontend/` com Next.js.

- diretório de deploy: `frontend`
- não usar SQL bruto no frontend
- não expor chaves sensíveis do Supabase fora do backend

## Documentação recomendada

- `STATE.md` — estado operacional auditado v98.0
- `ROADMAP.md` — roadmap limpo e pendências reais
- `docs/SYSTEM_CONTEXT.md` — mapa técnico atualizado
- `docs/ARCH_AUTOHEALING.md` — arquitetura de autocura e extração resiliente
- `docs/DOCUMENTATION_AUDIT.md` — classificação da documentação: válida, parcial, histórica ou lixo operacional
- `docs/index_documentacao.md` — índice de leitura

## Variáveis de ambiente de proxy (v98.0)

| Variável | Descrição | Exemplo |
|---|---|---|
| `PROXY_URL_TEMPLATE` | **Recomendado.** URL de proxy residencial com `{SESSION_ID}` para sticky binding por sessão | `http://user-res-session-{SESSION_ID}:senha@proxy.webshare.io:10000` |
| `PROXY_LIST` | Lista separada por vírgula de proxies em roundrobin (legado) | `http://p1:s@h:p,http://p2:s@h:p` |
| `PROXY_URL` | Proxy único fixo (legado) | `http://user:senha@proxy:3128` |

## Regras práticas

1. Considere `STATE.md` como fonte de verdade de operação.
2. Considere `ROADMAP.md` como fonte de verdade de planejamento.
3. Trate `docs/archive/` e specs antigas como histórico, não como contrato atual.
4. LiteRT não faz mais parte do pipeline de processamento ativo.
5. O classificador oficial em produção é `workers/processors/wk_classifica_comentarios.py`.
6. O Voyant Server (Java) e o `SaVoyant` foram totalmente expurgados na v96.2, substituídos pelo `SaFastDrop` (Python local).

## Observação importante

O repositório contém documentação histórica de várias fases. Parte dela continua útil como contexto, mas não representa mais o estado real do sistema. Consulte a auditoria em `docs/DOCUMENTATION_AUDIT.md` antes de usar documentos antigos como base de implementação.