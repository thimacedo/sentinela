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
2. `mistral`, `groq`, `openrouter` para refino cloud
3. `FallbackLLM` como recuperação de desastre

## 3. O que mudou na auditoria

- LiteRT foi removido da documentação central porque não está mais no processamento ativo
- PGMQ deixou de ser tratado como item implantado; hoje a fila distribuída real é a trava atômica da `fila_coleta`
- o frontend oficial é `frontend/`
- o watchdog local virou parte importante da operação diária

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

### Validação Executada
Rodamos o script `test_ai_service.py` que simulou chamadas com provedores de IA reais e de fallback. Durante o teste:
- O provedor `mistral` retornou erro `401 Unauthorized`.
- O sistema interceptou, acionou o Circuit Breaker e **podou permanentemente** o provedor da lista ativa.
- A requisição rotacionou com sucesso para o `groq_llama3` e obteve a classificação `DANO_A_IMAGEM` em JSON estruturado com sucesso absoluto.

## 8. Uso recomendado

Para iniciar trabalho novo:

1. leia `STATE.md`
2. leia `docs/SYSTEM_CONTEXT.md`
3. leia `ROADMAP.md`
4. valide no código