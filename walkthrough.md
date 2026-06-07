# Walkthrough — Estado Atual Auditável
_last_updated: 2026-06-04_

Este documento resume apenas o que continua válido após auditoria do código.

## 1. Pipeline ativo

- Watchdog supervisiona `main_runner.py`
- Orquestrador registra workers especializados
- `InstagramScraperWorker` coleta
- `AIProcessorWorker` classifica backlog e reanalisa baixa confiança
- `NetworkMiner` consolida rede
- `Treasurer` calcula indicadores
- `TargetResearchWorker` só entra no runtime quando `RESEARCHER_MODE` estiver habilitado

## 2. IA ativa

Camadas observadas no código:

1. `ollama` para triagem local
2. `maritaca` (Sabia-4) para auditoria e perícia cloud
3. `huggingface` via MCP para descoberta de modelos e datasets
4. `mistral`, `groq`, `openrouter` para refino e auditoria cruzada
5. `FallbackLLM` como recuperação de desastre

## 3. O que mudou na auditoria

- LiteRT foi removido da documentação central porque não está mais no processamento ativo
- PGMQ deixou de ser tratado como item implantado; hoje a fila distribuída real é a trava atômica da `fila_coleta`
- o frontend oficial é `frontend/`
- o watchdog local virou parte importante da operação diária
- **v90.4**: Implementada a supressão total de popups de console no Windows via `CREATE_NO_WINDOW`, garantindo operação silenciosa do orquestrador e subagentes.

## 4. Estado da fila

O código atual já suporta:

- claim atômico
- release atômico
- desbloqueio de lock expirado
- fallback para fluxo legado quando a RPC não existe

## 5. Estado da reclassificação

O script `scripts/reclassify_low_confidence.py`:

- prioriza cloud
- pode permitir fallback local com `ollama`
- não deve mais ser descrito como fluxo LiteRT/Ollama

## 6. Estado da refatoração de workers

Já foi concluído:

- expurgo dos entrypoints e contratos legados que competiam com o runtime moderno
- absorção da lógica útil do antigo `ClassifierWorker` em `core/ai_service.py`
- atualização dos scripts operacionais auxiliares
- desativação padrão do `researcher-01`

Ainda pendente:

- simplificar `workers/orchestrator/orchestrator.py`
- padronizar semântica de idle e `CycleResult`

## 7. Melhorias de Resiliência de Emergência (Fase 4.5)

Foram corrigidos e validados dois problemas operacionais observados nos logs do runner:
1. **Poda Automática para Erros 400 (Bad Request)**: Provedores de IA que retornarem `HTTP 400` (ex: chaves mal configuradas ou payloads incompatíveis, como verificado com `zhipu_glm4`) agora são removidos permanentemente da fila unificada em tempo de execução, em vez de ficarem retentando e gerando ruído de log.
2. **Timeout estendido no Playwright**: Aumentamos o timeout na etapa de navegação do `_verify_session` do Instagram de 30s para 45s, mitigando erros causados por instabilidade ou lentidão temporária da rede local.
3. **Mapeamento de Cores Semânticas de Badge**: Refatoramos o estilo de categoria para que a classificação `ERRO` seja renderizada de forma consistente em **Roxo (Purple)** no `local_dashboard.html` e no componente React `AnaliseTab.tsx`. Isso soluciona o problema onde erros eram coloridos de verde (Neutro) ou vermelho (Ódio), provendo uma distinção visual clara.
4. **Console de Logs Invertido (Recentes no Topo)**: Modificamos o console de logs no `local_dashboard.html` para realizar `prepend` (inserção no início do DOM) e remover os elementos excedentes do final. Isso faz com que as atualizações mais recentes fiquem fixadas no topo do painel, permitindo o acompanhamento em tempo real sem scroll.
5. **Persistência de Expurgos de IA (Configuração de Fallback)**: Comentamos os provedores de fallback comprovadamente inoperantes (`deepseek_chat`, `openrouter`, `google_gemini`, `zhipu_glm4`) no arquivo `config/fallback_providers.yaml`. Isso evita que eles sejam recarregados e tentados no boot inicial quando o runner python é reiniciado pelo watchdog.
6. **Prevenção de Erro 400 no DossierWorker**: Corrigimos a inicialização de `self._status_column` para `None` (em vez de `"status"`) no construtor do [dossier_worker.py](file:///c:/projetos/sentinela/workers/processors/dossier_worker.py#L36). Isso evita que o worker dispare uma query inicial inválida filtrando pela coluna `status` (inexistente) quando a tabela `dossies` do Supabase está vazia, o que causava um erro `HTTP 400 Bad Request`. O worker agora cai diretamente e de forma limpa no fallback seguro (`arquivo_path is null`).
7. **Limitação Vertical do Dashboard (Desktop)**: Adicionamos as classes `lg:h-screen lg:overflow-hidden` à tag `body` do [local_dashboard.html](file:///c:/projetos/sentinela/local_dashboard.html#L27) para fixar o layout à altura da tela (100vh) no ambiente desktop. Isso impede a barra de rolagem principal da página e permite que cada coluna realize rolagem interna independente, preservando a usabilidade no mobile.

### Validação Executada
Rodamos o script `test_ai_service.py` que simulou chamadas com provedores de IA reais e de fallback. Durante o teste:
- O provedor `mistral` retornou erro `401 Unauthorized`.
- O sistema interceptou, acionou o Circuit Breaker e **podou permanentemente** o provedor da lista ativa.
- A requisição rotacionou com sucesso para o `groq_llama3` e obteve a classificação `DANO_A_IMAGEM` em JSON estruturado com sucesso absoluto.

## 9. Consolidação de Subagentes, Sanitização e Auditoria de Custos (Fase Recente)

Nesta fase recente de saneamento técnico e monetização, realizamos melhorias críticas no monitoramento e nas garantias de conformidade do projeto:

1. **Verificação de Lint e Build do Frontend**:
   - Correção do erro no elemento SVG em [QueueTab.tsx](file:///c:/projetos/sentinela/frontend/components/warroom/QueueTab.tsx#L61) (substituindo `class` por `className`), o que resolveu o erro de type-checking do TypeScript.
   - Build do frontend (`npm run build`) validado e concluído com absoluto sucesso (100% estático e limpo).
2. **Mapeamento de Custos de IA (Burn Rate)**:
   - Implementação de gravação de log no [fallback_llm.py](file:///c:/projetos/sentinela/core/fallback_llm.py#L286) para persistir as estatísticas de chamadas bem-sucedidas e erros da malha de IA de fallback na tabela `fallback_logs` do Supabase.
   - Criação da lógica de cálculo financeiro `_compute_burn_rate()` no subagente [treasurer_agent.py](file:///c:/projetos/sentinela/workers/financial/treasurer_agent.py#L98) para estimar o custo financeiro operacional em USD gasto com chamadas de IA nas últimas 24 horas.
   - Integração da telemetria de burn rate nos relatórios e auditorias consolidadas pelo subagente financeiro.
3. **Purgação de Termos Proibidos**:
   - Expurgo dos termos juridicamente sensíveis ("forense", "prova", "evidência") e atualização de referências obsoletas em [api/index.py](file:///c:/projetos/sentinela/api/index.py#L262), [copilot-instructions.md](file:///c:/projetos/sentinela/copilot-instructions.md#L14), [docs/superpowers/plans/2026-05-16-otimizacao-ingestao-ia.md](file:///c:/projetos/sentinela/docs/superpowers/plans/2026-05-16-otimizacao-ingestao-ia.md), [docs/project_functions_v58.md](file:///c:/projetos/sentinela/docs/project_functions_v58.md#L17) e relatórios históricos de auditoria.
   - Exclusão de arquivos temporários e de log obsoletos da raiz do workspace (`tmp_litert_*.txt`).
4. **Vulnerabilidade Identificada no Supabase (RLS Desabilitado)**:
   - Identificação de que 15 tabelas no banco de dados remoto do Supabase estão com RLS (Row Level Security) desabilitado. O script de remediação foi apresentado para aprovação e posterior aplicação por parte do usuário.
5. **Monitoramento e Autocura do Pipeline**:
   - Criação do script de monitoramento e autocura [monitor_pipeline.py](file:///c:/projetos/sentinela/scratch/monitor_pipeline.py) que checa a porta `8001` (Watchdog) e interage via API HTTP (`/api/server/start`) ou subprocesso para restaurar o pipeline se inativo.
   - Agendamento da verificação periódica de status a cada 10 minutos (via cron do Antigravity).
   - Teste inicial validou o watchdog e o runner com sucesso completo (Status: `OPERACIONAL`, Score: `95.0`, Trust: `9.5`, Tier: `Gold`, DB/AI: `OK`).
6. **Resolução e Validação de Erros de Concorrência no Voyant (HTTPX)**:
   - Correção definitiva de `RuntimeError: Attempted to send a sync request with an AsyncClient instance` em [voyant_service.py](file:///c:/projetos/sentinela/core/voyant_service.py) e [validate_trombone.py](file:///c:/projetos/sentinela/scripts/validate_trombone.py) através da codificação manual do form body (`urllib.parse.urlencode`) transmitido via parâmetro `content`.
   - Executado teste de inicialização integrada do `VoyantServer.jar` local com o argumento obrigatório `headless=true`.
   - A validação oficial de contrato via [validate_trombone.py](file:///c:/projetos/sentinela/scripts/validate_trombone.py) completou com 100% de sucesso (5/5 verificações aprovadas), validando conectividade, extração de CorpusTerms (43 termos), cruzamento léxico de hostilidade (ratio 30.23%), e fast-drop de lote neutro (ratio 0.00%) sem falhas de encode Unicode.

## 8. Uso recomendado

Para iniciar trabalho novo:

1. leia `STATE.md`
2. leia `docs/SYSTEM_CONTEXT.md`
3. leia `ROADMAP.md`
4. valide no código