# AIProcessorWorker — Classificador Oficial de IA
_version: 88.0 | last_updated: 2026-06-04 | status: Ativo em Produção_

## 1. Visão Geral

**AIProcessorWorker** é o **classificador oficial** do pipeline PASA (Padrão de Análise de Sentimento Assistido). É o único worker responsável por classificar comentários em categorias de hostilidade política usando uma cascata resiliente de provedores de IA.

### Informações Básicas
- **ID do Worker**: Dinâmico (e.g., `ai-processor-01`)
- **Localização**: `workers/processors/ai_processor_worker.py`
- **Serviço Core**: `core/ai_service.py`
- **Status**: 🟢 Ativo em produção
- **Criticidade**: 🔴 **CRÍTICA** — Depende todo o pipeline de inteligência

### Funcionalidade Principal
1. **Classificação de Lote**: Processa comentários não classificados (`processado_ia=False`)
2. **Re-análise de Baixa Confiança**: Quando fila está vazia, refina comentários com confiança < 60%
3. **Cascata de Fallback**: Ollama (local) → Mistral → Groq → OpenRouter → Fallback profundo

---

## 2. Responsabilidades

### Responsabilidade 1: Classificação de Comentários
- **O quê**: Classificar comentários não processados em categorias PASA
- **De onde**: Tabela `comentarios` (filtro: `processado_ia=False`)
- **Processamento**: Lote de até `batch_size` comentários (default: 100)
- **Para onde**: Atualiza `categoria_ia`, `confianca_ia`, `analise_pericial` na tabela
- **Frequência**: Contínuo (um ciclo a cada ~45-60s em média)

### Responsabilidade 2: Re-análise de Baixa Confiança
- **Quando**: Quando a fila primária está vazia (`classified_count == 0`)
- **O quê**: Refina comentários com `confianca_ia < 0.6` (60%)
- **Objetivo**: Melhorar qualidade contínuamente
- **Limite**: `batch_size // 2` registros por ciclo
- **Saída**: Atualiza `confianca_ia` com novo valor

### Responsabilidade 3: Integração com Cascata de IA
- **Triagem Local**: Ollama filtra NEUTRO/LIXO rápido (< 2s)
- **Perícia Cloud**: Mistral/Groq/OpenRouter refinam suspeitos
- **Fallback Profundo**: FallbackLLM ativa se todos externos falharem
- **Circuit Breaker**: Desativa providers com taxa de erro alta

---

## 3. Arquitetura

### 3.1 Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────┐
│ AIProcessorWorker.run_cycle()                               │
├─────────────────────────────────────────────────────────────┤
│ 1. Detecta shutdown_event                                    │
│    └─ Se ativo: retorna CycleResult com erro                │
│                                                              │
│ 2. Executa ai_service.run_batch_classification()            │
│    └─ Retorna classified_count (comentários processados)    │
│                                                              │
│ 3. Se classified_count == 0:                                │
│    ├─ Executa ai_service.run_batch_reanalysis()            │
│    ├─ Limite: batch_size // 2                              │
│    └─ Retorna utility_count                                │
│                                                              │
│ 4. Se ambos == 0:                                           │
│    └─ Retorna CycleResult com erro="no_tasks_available"    │
│                                                              │
│ 5. Caso contrário:                                          │
│    └─ Retorna CycleResult com total_processed               │
│       └─ metadata: {"utility_tasks": utility_count}        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Camadas de IA (Cascata PASA v52.3)

#### **Camada 1: Triagem Local (Ollama)**
- **Modelo**: `OLLAMA_MODEL` (default: `qwen2.5:3b`)
- **Prompting**: `LOCAL_SYSTEM_PROMPT` (ultra-rápido)
- **Saída Esperada**: Binárias (NEUTRO, LIXO, SUSPEITO)
- **Tempo**: < 2s por comentário
- **Custo**: 🟢 Zero (local)
- **Quando Usar**: Sempre primeiro (antes de qualquer provider cloud)

```python
# Prompt de Triagem
LOCAL_SYSTEM_PROMPT = """
Você é um classificador binário de hostilidade política. 
Analise se o texto contém: insultos, ameaças, acusações ilícitas ou deslegitimação.
Responda APENAS com JSON:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO|LIXO|SUSPEITO",
  "confianca_ia": float,
  "analise_pericial": "Motivo rápido"
}
"""
```

#### **Camada 2: Perícia Cloud (Mistral → Groq → OpenRouter)**
- **Modelo Mistral**: `open-mistral-nemo` (ou fine-tuned)
- **Modelo Groq**: `llama-3.3-70b-versatile`
- **Modelo OpenRouter**: Roteamento dinâmico entre múltiplos
- **Saída**: Detalhada com 7 categorias PASA
- **Tempo**: 5-20s por comentário
- **Quando Usar**: Se Ollama retorna SUSPEITO
- **Timeout**: 15-20s por provider

#### **Camada 3: Fallback Profundo (FallbackLLM)**
- **Providers**: Cohere, DeepSeek, Cerebras, EdenAI, Replicate, etc.
- **Quando Usar**: Se Mistral, Groq, OpenRouter falham
- **Configuração**: `config/fallback_providers.yaml`
- **Status**: ⚠️ Pendente saneamento (alguns providers indisponíveis)

---

## 4. Ciclo de Execução

### Ciclo Padrão (com dados)

```
Ciclo 1, 2:15:34 PM
├─ Classificando lote de 100...
├─ Processadas 87 comentários
├─ Re-análise detectou 12 de baixa confiança
├─ Total processado: 99
└─ ✅ CycleResult: extracted=99, classified=99, duration=52.3s

Ciclo 2, 2:16:30 PM
├─ Classificando lote de 100...
├─ Processadas 45 comentários
├─ Re-análise detectou 8 de baixa confiança
├─ Total processado: 53
└─ ✅ CycleResult: extracted=53, classified=53, duration=38.1s
```

### Ciclo Vazio (sem dados)

```
Ciclo 15, 2:45:12 PM
├─ Classificando lote de 100...
├─ Processadas 0 comentários
├─ Fila primária vazia. Iniciando Re-análise...
├─ Re-análise encontrou 2 registros
├─ Total processado: 2
└─ ✅ CycleResult: extracted=2, classified=2, duration=12.4s

Ciclo 16, 2:46:08 PM
├─ Classificando lote de 100...
├─ Processadas 0 comentários
├─ Fila primária vazia. Iniciando Re-análise...
├─ Sem registros para refinar no momento
└─ ⚠️ CycleResult: error="no_tasks_available", extracted=0, duration=2.1s
```

### Ciclo com Erro

```
Ciclo 42, 3:15:44 PM
├─ Classificando lote de 100...
├─ 💥 Erro ao chamar Ollama: Connection timeout
├─ Tentando Mistral...
├─ 💥 Erro ao chamar Mistral: QUOTA_EXCEEDED
├─ Tentando Groq...
├─ ✅ Processadas 45 com Groq
└─ ⚠️ CycleResult: classified=45, error=None, warnings=["ollama_timeout", "mistral_quota"]
```

---

## 5. Categorias PASA

O AIProcessorWorker classifica comentários em 7 categorias:

### Se `is_hate = true`
| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| **ODIO_IDENTITARIO** | Ataques baseados em raça, religião, orientação sexual, misoginia, xenofobia | "Povo de [raça] deveria...", comentários racistas |
| **VIOLENCIA_GENERO** | Ofensas focadas em condição feminina | "Mulheres não devem...", assédio sexual |
| **AMEACA** | Incitação a dano físico, morte | "Deveria estar morto", ameaças diretas |
| **INSULTO_AD_HOMINEM** | Desumanização, baixo calão, ataques à honra | "Você é um imbecil", insultos |
| **ATAQUE_INSTITUCIONAL** | Deslegitimação de Estado, órgãos, democracia | "Judiciário é corrupto", "STF deveria ser dissolvido" |
| **DANO_A_IMAGEM** | Acusação de atos ilícitos, corrupção, crime | "Você roubou dinheiro público", acusações graves |

### Se `is_hate = false`
| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| **NEUTRO** | Engajamento legítimo, crítica técnica, slogans | "Vamos pra cima", apoio, questões normais |

---

## 6. Configuração

### 6.1 Variáveis de Ambiente

```bash
# IA
IA_PROVIDER=hybrid              # hybrid, ollama, groq, mistral
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b        # Modelo Ollama local
GROQ_API_KEY=gsk_xxxxx         # Groq API Key
MISTRAL_API_KEY=xxxxx          # Mistral API Key
OPENROUTER_API_KEY=sk-or-xxxxx # OpenRouter API Key

# IA Local
ENABLE_LOCAL_AI=true           # Ativar Ollama
CONFIDENCE_THRESHOLD=0.5       # Threshold para refino cloud
FINETUNED_MODEL_NAME=          # Modelo fine-tuned (opcional)

# Workers
RESEARCHER_MODE=disabled       # Worker de research
NUM_SCRAPER_WORKERS=1          # Número de scrapers
```

### 6.2 Configuração do Worker

No `main_runner.py`, ao registrar o worker:

```python
from workers.processors.ai_processor_worker import AIProcessorWorker

ai_worker = AIProcessorWorker(
    worker_id="ai-processor-01",
    config={
        "batch_size": 100,  # Comentários por ciclo
        "reanalysis_limit": 50,  # Limite de re-análise
        "confidence_threshold": 0.6  # Threshold para refino
    }
)
orch.register(ai_worker)
```

### 6.3 Circuit Breaker

```python
# core/circuit_breaker.py
ai_circuit_breaker.set_config(
    failure_threshold=5,     # Falhas antes de abrir
    recovery_timeout=60,     # Segundos antes de tentar
    half_open_max_calls=3    # Máximo de calls em half-open
)
```

---

## 7. Monitoramento

### 7.1 Logs Relevantes

```bash
# Ver logs do AIProcessorWorker
tail -f logs/main_runner.json | grep worker.ai_processor

# Ver categorias PASA processadas
tail -f logs/main_runner.json | grep "categoria_ia"

# Ver tempo de ciclo
tail -f logs/main_runner.json | grep "duration"
```

### 7.2 Métricas Expostas via API

```bash
# GET /api/v1/workers/ai-processor-01/stats
{
  "worker_name": "AIProcessorWorker",
  "cycles_total": 542,
  "cycles_successful": 538,
  "cycles_failed": 4,
  "items_processed": 45230,
  "average_cycle_duration_seconds": 52.3,
  "last_activity": "2026-06-04T14:32:00Z"
}
```

### 7.3 Dashboard Watchdog

```
Watchdog Dashboard → Workers Tab
├─ AIProcessorWorker
│  ├─ Status: 🟢 Active
│  ├─ Cycles: 542
│  ├─ Items: 45,230
│  ├─ Avg Duration: 52.3s
│  ├─ Last Cycle: 2 minutes ago
│  └─ Success Rate: 99.3%
```

---

## 8. Troubleshooting

### Problema 1: "Worker não está processando"

**Sintomas**:
- Ciclos executando mas `classified_count = 0` continuamente
- Dashboard mostra `items_processed` não aumentando

**Possíveis Causas**:
1. Não há comentários com `processado_ia = False` no banco
2. InstagramScraperWorker não está coletando
3. Banco de dados desconectado

**Solução**:
```bash
# 1. Verificar se há comentários não processados
python -c "
from core.db import supa
res = supa.table('comentarios').select('id', count='exact').eq('processado_ia', False).execute()
print(f'Comentários não processados: {res.count}')
"

# 2. Se vazio, reiniciar scrapers
# No dashboard: Workers → InstagramScraperWorker → Restart

# 3. Verificar logs de scraper
tail -f logs/main_runner.json | grep "worker.ig_v2"
```

### Problema 2: "Erro: Ollama não está respondendo"

**Sintomas**:
```
💥 Falha no provider 'ollama': Connection timeout
Tentando Mistral...
```

**Solução**:
```bash
# 1. Verificar se Ollama está rodando
curl http://localhost:11434/api/tags

# 2. Se não retornar, iniciar Ollama
ollama serve

# 3. Se ainda falhar, reiniciar container
docker restart ollama  # se usando Docker

# 4. Verificar modelo
ollama pull qwen2.5:3b
```

### Problema 3: "Groq/Mistral retorna QUOTA_EXCEEDED"

**Sintomas**:
```
Erro ao chamar groq: Error code: 429 - {message:'Rate limit exceeded'}
```

**Solução**:
```bash
# 1. Aguardar reset de quota (tipicamente 1 hora)
# 2. Verificar limites em:
#    - Groq: https://console.groq.com/
#    - Mistral: https://console.mistral.ai/

# 3. Usar fallback enquanto aguarda
# Editar IA_PROVIDER=ollama (apenas local)

# 4. Considerar upgrade de plano
```

### Problema 4: "Confiança muito baixa (< 40%)"

**Sintomas**:
```
Classificação concluída: categoria=DANO_A_IMAGEM, confianca=0.32
```

**Causa**: Modelo tem dúvida sobre classificação

**Solução**:
```bash
# 1. Dados será re-analisado próxima vez que fila esvaziar
# 2. Aumentar CONFIDENCE_THRESHOLD para forçar refino cloud
#    CONFIDENCE_THRESHOLD=0.7

# 3. Fine-tunar modelo localmente
#    Scripts: scripts/train_ia.py
```

---

## 9. Métricas & KPIs

### Métricas Primárias

| Métrica | Target | Alerta |
|---------|--------|--------|
| **Tempo de Ciclo** | 30-60s | > 120s |
| **Taxa de Sucesso** | > 99% | < 95% |
| **Items/Ciclo** | 50-150 | < 20 |
| **Confiança Média** | > 0.75 | < 0.60 |
| **Taxa de Erro** | < 1% | > 5% |

### Cálculos

```python
# Success Rate
success_rate = (cycles_successful / cycles_total) * 100

# Items per Hour
items_per_hour = (items_processed / total_hours) 

# Average Classification Time
avg_time_per_item = (total_duration / items_processed)

# Confidence Score
avg_confidence = sum(confianca_ia) / len(classificacoes)
```

---

## 10. Escalabilidade

### Aumentar Throughput

**Opção 1: Aumentar batch_size**
```python
config={"batch_size": 200}  # de 100 para 200
# Risco: Ciclos mais longos, menos responsivos
```

**Opção 2: Múltiplos AIProcessorWorkers**
```python
for i in range(3):
    worker = AIProcessorWorker(
        worker_id=f"ai-processor-{i:02d}",
        config={"batch_size": 100}
    )
    orch.register(worker)
```
- ✅ Paralelo
- ⚠️ Requer mais recursos de CPU/memória
- ⚠️ Aumenta requisições às APIs cloud

**Opção 3: Aumentar modelo Ollama**
```bash
# De qwen2.5:3b (3B parâmetros) para:
OLLAMA_MODEL=mistral:7b  # 7B parâmetros
# Vantagem: Melhor qualidade
# Desvantagem: 2x mais lento, 3x mais memória
```

---

## 11. Integração com Outros Componentes

### InstagramScraperWorker → AIProcessorWorker
```
1. Scraper coleta comentários
2. Insere em comentarios (processado_ia=False)
3. AIProcessorWorker detecta novos
4. Classifica
5. Atualiza comentarios (categoria_ia, confianca_ia)
```

### AIProcessorWorker → NetworkMinerWorker
```
1. AIProcessorWorker classifica comentários
2. Workers posteriores consomem categoria_ia
3. NetworkMinerWorker minera redes de hostilidade
4. Detecta clusters coordenados
```

### AIProcessorWorker → AlertWorker
```
1. AIProcessorWorker marca ODIO_IDENTITARIO
2. AlertWorker detecta PICOS
3. Envia alertas críticos (WhatsApp, email)
```

---

## 12. Dependências

### Dependências Internas
- `workers/base/worker_base.py` — Classe base do worker
- `workers/base/cycle_result.py` — Estrutura de resultado de ciclo
- `core/ai_service.py` — Serviço de IA (cascata de provedores)
- `core/circuit_breaker.py` — Circuit breaker para providers

### Dependências Externas
- **Ollama** — IA local (necessário se `IA_PROVIDER` inclui "ollama")
- **Groq API** — Provider cloud
- **Mistral API** — Provider cloud
- **OpenRouter API** — Agregador de provedores
- **Supabase** — Banco de dados

### Tabelas do Banco
- `comentarios` — Lê `processado_ia=False`, escreve `categoria_ia`, `confianca_ia`
- `candidatos` — Referência de alvos
- (Opcional) `worker_rewards` — Tracking de XP

---

## 13. Segurança

### Inputs Validados
```python
# Validação de texto
if not isinstance(text, str):
    text = str(text or "")
if len(text) > 8000:
    text = text[:8000]
```

### API Keys
- 🔴 **NUNCA** log `GROQ_API_KEY`, `MISTRAL_API_KEY`
- 🟢 Usar `os.getenv()` (carregado do `.env`)
- 🔴 **NUNCA** hardcoding

### Detecção de Prompt Injection
```python
# Safe decode para evitar Unicode bombs
def safe_decode_unicode(s: str) -> str:
    # ... validação robusta
```

---

## 14. Performance Tuning

### Para Classificações Mais Rápidas
```bash
# Usar Ollama apenas (sem cloud)
IA_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
```

### Para Classificações Mais Precisas
```bash
# Forçar perícia cloud para tudo
CONFIDENCE_THRESHOLD=0.0  # Sempre chamar cloud
OLLAMA_MODEL=mistral:7b   # Modelo maior localmente
```

### Para Melhor Balanço
```bash
# Híbrido recomendado
IA_PROVIDER=hybrid
OLLAMA_MODEL=mistral:7b
CONFIDENCE_THRESHOLD=0.6   # Cloud para dúvidas
```

---

## 15. Changelog

### v88.0 (Atual)
- [x] Classificador oficial consolidado
- [x] Cascata de fallback automática
- [x] Re-análise de baixa confiança
- [x] Circuit breaker para providers
- [x] Telemetria completa

### v87.0
- [x] Removido suporte a LiteRT
- [x] Descontinuado Gemini direto

### v85.12 (Anterior)
- [x] Tarefa de utilidade de re-análise
- [x] Integração com PASA v85.3

---

## Referências

- **Código**: [`workers/processors/ai_processor_worker.py`](../../../workers/processors/ai_processor_worker.py)
- **IA Service**: [`core/ai_service.py`](../../../core/ai_service.py)
- **Documentação PASA**: [`docs/PADRONIZACAO_LINGUISTICA_FORENSE.md`](../PADRONIZACAO_LINGUISTICA_FORENSE.md)
- **Configuração**: [`docs/ENVIRONMENT_VARIABLES.md`](../ENVIRONMENT_VARIABLES.md)

---

**Status**: ✅ Documentação Completa
**Última Revisão**: 2026-06-04
**Próxima Revisão**: Após mudanças no ai_service.py ou fallback_providers.yaml
