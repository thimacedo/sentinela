# WkClassificaComentarios — Classificador Oficial de IA
_version: 90.8 | last_updated: 2026-06-07 | status: Ativo em Produção_

## 1. Visão Geral

**WkClassificaComentarios** é o **classificador oficial** do pipeline PASA (Padrão de Análise de Sentimento Assistido). É o único worker responsável por classificar comentários em categorias de hostilidade política usando uma cascata resiliente de provedores de IA.

### Informações Básicas
- **ID do Worker**: Dinâmico (e.g., `ai-processor-01`)
- **Localização**: `workers/processors/wk_classifica_comentarios.py`
- **Serviço Core**: `core/ai_service.py`
- **Status**: 🟢 Ativo em produção
- **Criticidade**: 🔴 **CRÍTICA** — Todo o pipeline de inteligência depende deste worker

### Funcionalidade Principal
1. **Classificação de Lote**: Processa comentários não classificados (`processado_ia=False`)
2. **Re-análise de Baixa Confiança**: Quando fila está vazia, refina comentários com confiança < 60%
3. **Cascata de Fallback**: Ollama (local) → Sabia-4 (Maritaca) → Mistral → Groq → OpenRouter → FallbackLLM
4. **Pipeline Reativo (Fase 9)**: Acoplado ao `EventBus` — reage a `NEW_DATA_AVAILABLE` sem polling constante

---

## 2. Responsabilidades

### Responsabilidade 1: Classificação de Comentários
- **O quê**: Classificar comentários não processados em categorias PASA
- **De onde**: Tabela `comentarios` (filtro: `processado_ia=False`)
- **Processamento**: Lote de até `batch_size` comentários (default: 100)
- **Para onde**: Atualiza `categoria_ia`, `confianca_ia`, `audit_data` na tabela
- **Frequência**: Contínua reativa via EventBus (timeout de segurança: 1200s)

### Responsabilidade 2: Re-análise de Baixa Confiança
- **Quando**: Quando a fila primária está vazia (`classified_count == 0`)
- **O quê**: Refina comentários com `confianca_ia < 0.6` (60%)
- **Objetivo**: Melhorar qualidade analítica continuamente
- **Limite**: `batch_size // 2` registros por ciclo
- **Nota**: Reanálise foi **desacoplada** do termômetro de alvos — temperatura (Frio/Morno/Quente) é atualizada exclusivamente durante ciclos de coleta

### Responsabilidade 3: Integração com Cascata de IA
- **Triagem Local**: Ollama filtra NEUTRO/LIXO/SUSPEITO rápido (< 2s)
- **Perícia Cloud**: Sabia-4 (Maritaca Sabia-4) → Mistral → Groq refinam suspeitos
- **Fallback Profundo**: FallbackLLM ativa se todos externos falharem
- **Circuit Breaker**: Providers com erro 401/403/429 são removidos/suspensos da malha em tempo real

---

## 3. Arquitetura

### 3.1 Pipeline Reativo (Fase 9 — Event-Driven)

O `WkClassificaComentarios` opera em modelo **reativo/event-driven**, não polling. O `EventBus` (`core.event_bus`) conecta o scraper ao classificador via sinalização em memória:

```
[InstagramScraperWorker] coleta dado
    ↓ NEW_DATA_AVAILABLE event
[EventBus] sinaliza em memória (~2ms overhead)
    ↓
[WkClassificaComentarios] acorda via event.wait()
    ↓
[Classificação Cascade] Ollama → Cloud (Sabia-4/Mistral/Groq)
    ↓
[comentarios] atualizados + event NEW_CLASSIFICATION_AVAILABLE
```

Timeouts de segurança: 1200s para evitar ciclos órfãos. Quando a fila primária está vazia, o worker entra em modo de reanálise de baixa confiança.

### 3.2 Camadas de IA (Cascata PASA v88.2)

#### **Camada 1: Triagem Local (Ollama)**
- **Modelo**: `OLLAMA_MODEL` (default: `llama3.2:1b`)
- **Prompting**: prompt reduzido otimizado para triagem (< 2s por comentário)
- **Saída Esperada**: Binárias (NEUTRO, LIXO, SUSPEITO)
- **Custo**: 🟢 Zero (local)
- **Estratégia**: Marca como `"SUSPEITO"` qualquer comentário com desvios léxicos ou ofensas para revisão cloud

#### **Camada 2: Perícia Cloud**
- **Primário**: Sabia-4 (Maritaca, 60 RPM) — via `MARITACA_API_KEY`
- **Fallbacks**: Mistral → Groq → OpenRouter
- **Saída**: 7 categorias PASA detalhadas
- **Timeout**: 15-20s por provider
- **Backoff 429**: 300s (5 minutos) para rate limits

#### **Camada 3: Fallback Profundo (FallbackLLM)**
- **Providers**: Cohere, DeepSeek, Cerebras, etc.
- **Configuração**: `config/fallback_providers.yaml`
- **Ativação**: Apenas quando toda a malha cloud falha

### 3.3 Fluxo de Execução (código real)

```
WkClassificaComentarios.run_cycle()
  1. Verifica shutdown_event → aborta se ativo
  2. Executa ai_service.run_batch_classification()
     └─ Retorna classified_count
  3. Se classified_count == 0:
     ├─ Executa ai_service.run_batch_reanalysis()
     └─ Limite: batch_size // 2
  4. Se ambos == 0 → CycleResult(error="no_tasks_available")
  5. Caso contrário → CycleResult(total_processed, metadata)
```

---

## 4. Categorias PASA

### Se `is_hate = true`
| Categoria | Descrição |
|-----------|-----------|
| **ODIO_IDENTITARIO** | Ataques baseados em raça, religião, orientação sexual, misoginia, xenofobia |
| **VIOLENCIA_GENERO** | Ofensas focadas em condição feminina |
| **AMEACA** | Incitação a dano físico, morte |
| **INSULTO_AD_HOMINEM** | Desumanização, ataques à honra |
| **ATAQUE_INSTITUCIONAL** | Deslegitimação de Estado, STF, democracia |
| **DANO_A_IMAGEM** | Acusação de atos ilícitos, corrupção, crime |

### Se `is_hate = false`
| Categoria | Descrição |
|-----------|-----------|
| **NEUTRO** | Engajamento legítimo, crítica técnica, slogans |

---

## 5. Configuração

### Variáveis de Ambiente

```bash
# IA Local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# IA Cloud
MARITACA_API_KEY=        # Sabia-4 — primário em produção
MISTRAL_API_KEY=         # Fallback cloud
GROQ_API_KEY=            # Fallback cloud
OPENROUTER_API_KEY=      # Fallback cloud

# Workers
NUM_AI_WORKERS=2         # Escalonamento horizontal (default: 2 instâncias)
RESEARCHER_MODE=disabled
```

### Batch Processing (v90.0)

O endpoint de classificação processa batches concorrentemente com `asyncio.Semaphore(5)`, limitando pressão sobre APIs pagas:

```python
# workers/processors/wk_classifica_comentarios.py
batch_size = config.get("batch_size", 100)  # default 100 por ciclo
```

---

## 6. Monitoramento

### Logs
```bash
# Ver logs de classificação
tail -f logs/main_runner.json | grep "worker.ai_processor"

# Ver falhas de provider
tail -f logs/main_runner.json | grep "circuit_breaker"
```

### Dashboard Watchdog
```
Watchdog → Workers Tab
├─ WkClassificaComentarios
│  ├─ Status: 🟢 Active
│  ├─ Cycles: N
│  ├─ Items: NNN
│  ├─ Last Cycle: X minutes ago
│  └─ AI Mesh: (verde/amarelo/vermelho)
```

---

## 7. Troubleshooting

### "Worker não processa — classified_count = 0 continuamente"
1. Verificar se há comentários com `processado_ia = False`:
   ```sql
   SELECT COUNT(*) FROM comentarios WHERE processado_ia = false;
   ```
2. Verificar se o scraper está coletando (fila `fila_coleta` ativa)
3. Verificar logs: `grep "worker.ai_processor" logs/main_runner.json`

### "Ollama não responde"
```bash
curl http://localhost:11434/api/tags
# Se vazio: ollama serve
# Verificar modelo:
ollama list
ollama pull llama3.2:1b
```

### "Todos os providers cloud falham (403/429)"
- Circuit Breaker remove providers com erro 401/403/402 permanentemente
- Providers com 429 ficam suspensos por 300s
- Sistema continua operando com Ollama local e FallbackLLM
- Monitorar malha via dashboard watchdog (seção "Malha Degradada")

---

## 8. Escalabilidade

### Horizontal (v90.0)
```python
# main_runner.py — múltiplas instâncias
NUM_AI_WORKERS=2  # duplica throughput de classificação
```

### Batch Processing
```python
# Semáforo controla concorrência de chamadas cloud
asyncio.Semaphore(5)  # máximo 5 chamadas paralelas por worker
```

---

## 9. Integração com Outros Componentes

```
InstagramScraperWorker → EventBus → WkClassificaComentarios → comentarios
WkClassificaComentarios → SaMineracaoRedes (reativo)
WkClassificaComentarios → SaAuditoriaFinanceira (reativo)
WkClassificaComentarios → SaRevisaoOnline (cloud para suspeitos)
```

### EventBus (Fase 9)
- `NEW_DATA_AVAILABLE` — dispara classificação
- `NEW_CLASSIFICATION_AVAILABLE` — acordado por outros subagentes
- Overhead real: ~2ms por sinal

---

## 10. Dependências

- `workers/base/worker_base.py` — Classe base
- `workers/base/cycle_result.py` — Estrutura de resultado
- `core/ai_service.py` — Cascata de provedores
- `core/event_bus.py` — EventBus reativo (Fase 9)
- `core/circuit_breaker.py` — Circuit breaker para providers
- `docs/PADRONIZACAO_LINGUISTICA_ANALITICA.md` — Metodologia Vichi-Sentinela

---

## 11. Changelog

### v90.8 (2026-06-07)
- [x] Corrigido path de arquivo: `workers/processors/wk_classifica_comentarios.py`
- [x] Classe renomeada: `WkClassificaComentarios`
- [x] Cascade atualizada: Sabia-4 (Maritaca) como primário cloud
- [x] Pipeline reativo (EventBus) documentado (Fase 9)
- [x] Backoff 429 aumentado para 300s

### v90.0 (2026-06-05)
- [x] Batch processing concorrente com semáforo
- [x] Escalonamento horizontal (NUM_AI_WORKERS=2)

### v88.0
- [x] ClassifierWorker removido; WkClassificaComentarios oficial
- [x] LiteRT removido do pipeline

---

**Status**: ✅ Documentação Revisada
**Última Revisão**: 2026-06-07
**Fonte de verdade**: `STATE.md`, `ROADMAP.md`, `docs/DOCUMENTATION_AUDIT.md`
