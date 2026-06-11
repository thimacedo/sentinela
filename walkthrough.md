# Walkthrough — Estado Atual Auditável
_last_updated: 2026-06-11_

Este documento resume apenas o que continua válido após auditoria do código.

## 1. Pipeline ativo

- Watchdog supervisiona `main_runner.py`
- Orquestrador registra workers especializados:
  - `WkColetaInstagram` (coleta do Instagram)
  - `WkClassificaComentarios` (classificador oficial do pipeline via IA)
  - `SaRevisaoOnline` (revisão de comentários de baixa confiança na nuvem)
  - `SaFastDrop` (pré-triagem léxica local, zero Java, zero LLM)
- `WkPesquisaAlvos` (pesquisa de alvos) só entra no runtime se `RESEARCHER_MODE` estiver habilitado
- `AutopilotManager.pulse()` em background supervisiona a saúde do sistema e delega autocura ao `SREAgent`
- `WkAplicaSugestoes.start()` em background aplica automaticamente correções de configuração a cada 10 minutos
- `CloudListener.start()` fornece batimentos cardíacos (heartbeat) e aceita comandos remotos

## 2. IA ativa

Camadas observadas no código:

1. `ollama` para triagem local (opcional)
2. `maritaca` (Sabia-4) para auditoria e perícia cloud
3. `huggingface` via MCP para descoberta de modelos e datasets
4. `mistral`, `groq`, `openrouter` para refino e auditoria cruzada
5. `FallbackLLM` como recuperação de desastre

## 3. O que mudou na auditoria (v96.0)

- **Watchdog como Agente SRE Autônomo**: O `AutopilotManager` procedimental foi convertido em um **Agente de SRE Autônomo** (`core/autopilot/sre_agent.py`). O agente possui um registro de ferramentas de controle do sistema (**Tool Calling**) que executa ações como reiniciar workers específicos, reiniciar o main_runner inteiro, colocar alvos problemáticos em cooldown temporário no banco de dados, e rotacionar chaves de sessões.
- **Loop Cognitivo OODA Híbrido**: O agente resolve erros comuns localmente por regras (0 tokens) e consulta a malha de IA (Gemini/Mistral em JSON) de forma estritamente reativa sob degradação complexa (`DOM_CHANGE` ou `UNKNOWN`), garantindo burn rate mínimo de tokens.
- **Desativação Completa do VoyantServer (Java)**: O thread de inicialização de `VoyantServer.jar` (JVM) foi removido do watchdog, cortando de vez todo o vazamento de recursos no boot.
- **Validação de SRE**: Adicionado o script de teste de SRE ([test_sre_agent.py](file:///c:/Projetos/sentinela/scratch/test_sre_agent.py)) validado com 100% de sucesso.
- **Expurgo do Java VoyantServer**: O subagente `SaVoyant` foi removido e desativado. Substituído por completo pelo `SaFastDrop` (`workers/ai/sa_fast_drop.py`) que usa processamento de string puro local (`core/lexical_filter.py`), sem qualquer dependência de JVM/HTTP e com custo zero de tokens.
- **Advisor Determinístico (Zero Tokens)**: O `SaDiagnosticaSistemas` e a classe `Diagnostician` foram refatorados para analisar erros comuns por meio de regras determinísticas locais e dicionários de sugestões pré-fabricadas.
- **Autocura Acelerada**: O intervalo de execução do worker `WkAplicaSugestoes` foi reduzido de 30 minutos para 10 minutos.
- **Faxina Arquitetural de Arquivos Órfãos**: 8 arquivos obsoletos em `core/` sem qualquer importação ativa no runtime foram purgados definitivamente.
- **Correção de NameError**: Corrigida a importação em falta do `WkAplicaSugestoes` no boot do `main_runner.py`.

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

## 7. Uso recomendado

Para iniciar trabalho novo:

1. leia `STATE.md`
2. leia `docs/SYSTEM_CONTEXT.md`
3. leia `ROADMAP.md`
4. valide no código