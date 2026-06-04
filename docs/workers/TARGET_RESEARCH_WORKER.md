# TargetResearchWorker - Documentação Completa

**Versão:** PASA v84.16  
**Arquivo Fonte:** `/workspace/workers/ai/target_research_worker.py`  
**Status:** ✅ Em Produção (Opcional, controlado por RESEARCHER_MODE)  
**Última Atualização:** Junho 2026

---

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Responsabilidades Funcionais](#responsabilidades-funcionais)
3. [Arquitetura e Design](#arquitetura-e-design)
4. [Ciclo de Execução](#ciclo-de-execução)
5. [Modo de Operação](#modo-de-operação)
6. [Serviço de Inteligência](#serviço-de-inteligência)
7. [Sistema de Priorização](#sistema-de-priorização)
8. [Configuração](#configuração)
9. [Integração com Banco de Dados](#integração-com-banco-de-dados)
10. [Monitoramento e Observabilidade](#monitoramento-e-observabilidade)
11. [Troubleshooting](#troubleshooting)
12. [Métricas e KPIs](#métricas-e-kpis)
13. [Escalabilidade](#escalabilidade)
14. [Integração com Outros Componentes](#integração-com-outros-componentes)
15. [Dependências Externas](#dependências-externas)

---

## 🎯 Visão Geral

O **TargetResearchWorker** é um curador especializado em **validação de identidade** e **enriquecimento de metadados** para alvos (candidatos, políticos) monitorados na plataforma Sentinela.

### Responsabilidades Principais

- **Validação de Identidade:** Verificar se o candidato monitorado é realmente quem diz ser
- **Enriquecimento de Dados:** Atualizar campos faltantes (bio, seguidores, etc)
- **Priorização Inteligente:** Focar primeiro em alvos "Ativos" sem validação
- **Sistema de Recompensa:** Ganhar XP baseado em qualidade de validação

### Necessidade de Negócio

Monitorar candidatos incorretos (contas fake, clones, impersonadores) prejudica a análise. O TargetResearchWorker assegura que:
- Apenas alvos reais são monitorados
- Dados de candidatos estão sempre atualizados
- Inteligência humana/IA valida automaticamente

---

## 🔄 Responsabilidades Funcionais

| Responsabilidade | Descrição |
|---|---|
| **Busca de Alvos Pendentes** | Procura candidatos com `status_monitoramento='Ativo'` e `identidade_validada=null` |
| **Validação de Identidade** | Executa serviço de inteligência para confirmar identidade |
| **Enriquecimento** | Atualiza meta dados (bio, seguidores, etc) quando disponível |
| **Priorização** | Ordena por `nota_relevancia` DESC para alvos mais importantes |
| **Modo Utilidade** | Se fila de validação está vazia, enriquece dados faltantes |
| **Cálculo de Qualidade** | Avalia qualidade da validação (0.0-1.0) |
| **Recompensa XP** | Distribui XP baseado em qualidade e sucesso |

---

## 🏗️ Arquitetura e Design

### Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SETUP                                                        │
│   • Inicializa logger                                           │
│   • Verifica RESEARCHER_MODE                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. VALIDAÇÃO DE MODO (run_cycle)                                │
│   • Se mode="disabled": retorna error="disabled"               │
│   • Se mode="validation": foca em identidade_validada=null     │
│   • Se mode="utility": enriquecimento de dados                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. BUSCA DE ALVO PRIORITÁRIO                                    │
│   • Query: candidatos com status_monitoramento='Ativo'         │
│   • Filtro: identidade_validada IS NULL                        │
│   • Ordem: nota_relevancia DESC                                │
│   • Limite: 1 alvo por ciclo                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. FALLBACK PARA MODO UTILIDADE                                 │
│   • Se nenhum alvo encontrado E mode='utility':               │
│   • Busca candidatos com bio vazia OU seguidores=0             │
│   • Ordena por atualizado_em ASC (menos recentes primeiro)     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. PROCESSAMENTO VIA INTELIGÊNCIA                               │
│   • Chama intelligence_service.research_and_validate()         │
│   • Retorna dados com "_quality" score                          │
│   • Extracted += 1 (sucesso)                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. CÁLCULO DE QUALIDADE E RECOMPENSA                            │
│   • quality_score = data.get("_quality", 0.5)                 │
│   • Se quality > 0.8: xp_delta = 15.0 (excelente)             │
│   • Se extracted > 0 mas quality ≤ 0.8: xp_delta = 5.0        │
│   • Se nenhum alvo: xp_delta = -5.0 (penalidade)              │
│   • Se no_tasks_available: xp_delta = 0.0 (neutro)            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. RETORNO DE CYCLERESULT                                       │
│   • Inclui target (username do alvo)                           │
│   • Inclui metadata com xp_delta e quality                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. TEARDOWN                                                     │
│   • Log de encerramento                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Camadas de Processamento

1. **Camada de Filtragem** → Query Supabase com priorização
2. **Camada de Inteligência** → IntelligenceService (IA/Pesquisa)
3. **Camada de Enriquecimento** → Atualizar dados faltantes
4. **Camada de Scoring** → Cálculo de qualidade (0.0-1.0)
5. **Camada de Recompensa** → Sistema de XP

---

## ⏱️ Ciclo de Execução

### Exemplo: Ciclo em Modo "validation" (Normal)

```
[2026-06-04 10:00:00] INFO worker.researcher: [Curador] researcher_1 pronto.
[2026-06-04 10:01:00] INFO worker.researcher: [Curador] Processando (Utilidade/Validação): @usuario_candidato_123
[2026-06-04 10:01:05] INFO worker.researcher: Ciclo #1: extracted=1, quality=0.92, xp_delta=15.0 ✅
```

### Exemplo: Ciclo em Modo "utility" (Enriquecimento)

```
[2026-06-04 10:02:00] INFO worker.researcher: [Curador] Fila de validação vazia. Iniciando Enriquecimento de Metadados...
[2026-06-04 10:02:00] INFO worker.researcher: [Curador] Processando (Utilidade/Validação): @usuario_candidato_456
[2026-06-04 10:02:03] INFO worker.researcher: Ciclo #2: extracted=1, quality=0.65, xp_delta=5.0 ⚠️
```

### Exemplo: Ciclo em Modo "disabled"

```
[2026-06-04 10:03:00] INFO worker.researcher: [Curador] researcher_1 pronto.
[2026-06-04 10:03:01] INFO worker.researcher: Ciclo #3: error="disabled", simulated=True
```

---

## 🎛️ Modo de Operação

### 1. Modo "disabled" (Padrão)

```python
if self.mode == "disabled":
    return CycleResult(
        error="disabled",
        simulated=True,
        metadata={"reason": "researcher_disabled"}
    )
```

**Comportamento:** Worker não faz nada, retorna ciclo vazio.  
**Uso:** Quando não há necessidade de validação de identidade.

### 2. Modo "validation" (Prioridade 1)

```python
# Busca alvos pendentes de validação
res = db_client.client.table('candidatos')\
    .filter('status_monitoramento', 'ilike', 'Ativo')\
    .is_('identidade_validada', 'null')\
    .order('nota_relevancia', desc=True)\
    .limit(1)\
    .execute()
```

**Objetivo:** Validar identidade de candidatos monitorados.  
**Foco:** Alvos "Ativos" sem validação, ordenados por importância.  
**Prioridade:** ALTA (sempre executado primeiro)

### 3. Modo "utility" (Prioridade 2)

```python
# Se fila de validação vazia, enriquecer dados
if not res.data and self.mode == "utility":
    res = db_client.client.table('candidatos')\
        .filter('status_monitoramento', 'ilike', 'Ativo')\
        .or_('bio.is.null,seguidores.eq.0')\
        .order('atualizado_em', desc=False)\
        .limit(1)\
        .execute()
```

**Objetivo:** Manter dados de candidatos atualizados.  
**Foco:** Candidates com bio vazia OU seguidores=0.  
**Prioridade:** MÉDIA (após fila de validação esvaziar)

### Seleção de Modo

```python
self.mode = config.get("mode", os.getenv("RESEARCHER_MODE", "disabled")).strip().lower()
```

**Ordem de Preferência:**
1. `config.get("mode")` (passado ao __init__)
2. `os.getenv("RESEARCHER_MODE")` (variável de ambiente)
3. `"disabled"` (padrão)

---

## 🧠 Serviço de Inteligência

### IntelligenceService

O TargetResearchWorker delega validação ao `intelligence_service`:

```python
data = await intelligence_service.research_and_validate(target_username)
```

**Responsabilidade da Service:**
- Pesquisar identidade do candidato (múltiplas fontes)
- Validar se é conta legítima
- Retornar dados estruturados com score de qualidade

**Resposta Esperada:**

```python
{
    "username": "usuario_candidato",
    "nome_completo": "João Silva",
    "bio": "Candidato a deputado...",
    "seguidores": 50000,
    "verificado": True,
    "links_validacao": ["wikipedia", "site_oficial"],
    "_quality": 0.92  # Score 0.0-1.0
}
```

### Campo "_quality"

Métrica de confiança da validação:
- **0.9-1.0:** Excelente (conta oficial verificada, múltiplas fontes confirmam)
- **0.7-0.8:** Bom (razoável confiança)
- **0.5-0.6:** Aceitável (alguns sinais positivos)
- **< 0.5:** Fraco (dados insuficientes)

---

## 🎯 Sistema de Priorização

### Prioridade de Alvos (CRÍTICA)

```
1. Candidatos Ativos SEM validação (identidade_validada IS NULL)
   └─ Ordenados por nota_relevancia DESC
   └─ Exemplo: Candidato a presidente → Candidato a vereador

2. Se fila #1 vazia E modo="utility":
   └─ Candidatos com bio vazia OU seguidores=0
   └─ Ordenados por atualizado_em ASC (menos recentes primeiro)
```

### Exemplo: Dados de Candidatos

```python
# Alvo 1 (Prioridade Alta)
{
    "username": "presidente_2026",
    "status_monitoramento": "Ativo",
    "identidade_validada": null,  # ← Pendente!
    "nota_relevancia": 100        # ← Alta importância
}

# Alvo 2 (Prioridade Média)
{
    "username": "vereador_sp",
    "status_monitoramento": "Ativo",
    "identidade_validada": null,  # ← Pendente!
    "nota_relevancia": 40         # ← Menor importância
}

# Alvo 3 (Utilidade)
{
    "username": "candidato_antigo",
    "status_monitoramento": "Ativo",
    "identidade_validada": "2026-05-01",  # ← Já validado
    "bio": null,                           # ← Dados incompletos
    "seguidores": 0,
    "atualizado_em": "2026-01-15"         # ← Desatualizado
}
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `RESEARCHER_MODE` | str | "disabled" | Modo de operação: disabled, validation, utility |

### Parâmetros de Configuração (Config Dict)

```python
config = {
    "mode": "validation"  # Sobrescreve RESEARCHER_MODE
}
```

### Hardcoded Thresholds

| Threshold | Valor | Propósito |
|-----------|-------|----------|
| `quality_threshold_high` | 0.8 | Acima = XP +15.0 |
| `quality_threshold_medium` | 0.0 | Abaixo = XP -5.0 |
| `xp_excellent` | 15.0 | Validação excelente |
| `xp_good` | 5.0 | Validação boa |
| `xp_fail` | -5.0 | Falha (não encontrou alvo) |
| `xp_neutral` | 0.0 | Sem tarefas (neutro) |

### Exemplo de Inicialização

```python
from workers.ai.target_research_worker import TargetResearchWorker

config = {"mode": "validation"}

worker = TargetResearchWorker(
    worker_id="researcher_1",
    config=config
)

await worker.setup()
for _ in range(100):
    result = await worker.run_cycle()
    print(f"Ciclo: {result.cycle}, Target: {result.target}, XP: {result.metadata['xp_delta']}")
await worker.teardown()
```

---

## 🗄️ Integração com Banco de Dados

### Tabelas Utilizadas

#### 1. `candidatos` (Read)
- **Propósito:** Buscar alvos para validação/enriquecimento
- **Operação:** SELECT
- **Filtros:** 
  - Prioridade 1: `status_monitoramento='Ativo'`, `identidade_validada IS NULL`
  - Prioridade 2: `bio IS NULL` OR `seguidores=0`, `atualizado_em` antigo
- **Frequência:** A cada ciclo

### Queries

```python
# PRIORIDADE 1: Validação de identidade
res = db_client.client.table('candidatos')\
    .select('username')\
    .filter('status_monitoramento', 'ilike', 'Ativo')\
    .is_('identidade_validada', 'null')\
    .order('nota_relevancia', desc=True)\
    .limit(1)\
    .execute()

# PRIORIDADE 2: Enriquecimento (Fallback)
res = db_client.client.table('candidatos')\
    .select('username')\
    .filter('status_monitoramento', 'ilike', 'Ativo')\
    .or_('bio.is.null,seguidores.eq.0')\
    .order('atualizado_em', desc=False)\
    .limit(1)\
    .execute()
```

### Performance

- **Índices Recomendados:**
  - `candidatos(status_monitoramento, identidade_validada, nota_relevancia DESC)`
  - `candidatos(bio, seguidores, atualizado_em)`

- **Limite:** 1 alvo por ciclo (muito eficiente)

---

## 📊 Monitoramento e Observabilidade

### Logs Emitidos

```
[Curador] {worker_id} pronto.
   └─ Emitido em: setup()
   └─ Nível: INFO

[Curador] Processando (Utilidade/Validação): @{username}
   └─ Emitido em: run_cycle()
   └─ Nível: INFO
   └─ Quando: Alvo encontrado e processado

[Curador] Fila de validação vazia. Iniciando Enriquecimento de Metadados...
   └─ Emitido em: run_cycle()
   └─ Nível: INFO
   └─ Quando: Modo utility, transição para enriquecimento

Erro na curadoria: {erro}
   └─ Emitido em: run_cycle()
   └─ Nível: ERROR

[Curador] {worker_id} encerrado.
   └─ Emitido em: teardown()
   └─ Nível: INFO
```

### Métricas Retornadas (CycleResult)

```python
CycleResult(
    worker_id=self.worker_id,
    cycle=self.cycle,
    target=target_username,      # username processado ou None
    source="intelligence_curation",
    extracted=extracted,          # 0 ou 1 (alvo processado)
    db_success=extracted > 0,     # True se alvo encontrado e processado
    classifier_success=extracted > 0,
    duration=elapsed_seconds,
    error=error,                  # None ou "disabled", "no_tasks_available", exc
    metadata={
        "xp_delta": float,        # Recompensa (-5.0 a 15.0)
        "quality": float          # Score de qualidade (0.0 a 1.0)
    }
)
```

---

## 🔧 Troubleshooting

### Problema 1: Worker em Modo "disabled"

**Sintoma:**
```
error="disabled", simulated=True
```

**Solução:**
1. Verificar RESEARCHER_MODE:
   ```bash
   echo $RESEARCHER_MODE
   ```

2. Se vazio ou "disabled", definir:
   ```bash
   export RESEARCHER_MODE=validation
   ```

3. Ou passar via config:
   ```python
   config = {"mode": "validation"}
   worker = TargetResearchWorker("researcher_1", config)
   ```

---

### Problema 2: Nenhum Alvo Encontrado (no_tasks_available)

**Sintoma:**
```
error="no_tasks_available", extracted=0
```

**Causas Possíveis:**
- Todos os alvos "Ativos" já foram validados
- Não há candidatos com `status_monitoramento='Ativo'`

**Solução:**
1. Verificar candidatos no banco:
   ```sql
   SELECT username, status_monitoramento, identidade_validada 
   FROM candidatos 
   WHERE status_monitoramento = 'Ativo';
   ```

2. Se vazio, adicionar candidatos de teste

3. Se fila vazia, isso é normal — worker foi bem (validou todos!)

---

### Problema 3: IntelligenceService Lança Exceção

**Sintoma:**
```
ERROR: Erro na curadoria: [Exception Message]
```

**Causas Possíveis:**
- IntelligenceService não está disponível
- Erro de rede (não conseguiu pesquisar)
- Dados inválidos do username

**Solução:**
1. Verificar se IntelligenceService está rodando
2. Validar username no banco (sem caracteres especiais)
3. Adicionar retry na service

---

## 📈 Métricas e KPIs

### Métricas de Qualidade

| Métrica | Definição | Target |
|---------|-----------|--------|
| Taxa de Validação | `(extracted > 0) ? 1 : 0` | > 80% de ciclos |
| Qualidade Média | Média de `quality_score` | > 0.75 |
| Taxa Excelente | `(quality > 0.8) / ciclos` | > 60% |
| Tempo por Alvo | `duration / extracted` | < 10s |

### Alertas Recomendados

- 🟡 **Taxa de Validação < 50%:** Problemas com InteligenceService ou dados
- 🟡 **Qualidade Média < 0.5:** Serviço de pesquisa degradado

---

## 🚀 Escalabilidade

### Limitações Atuais

- 1 alvo por ciclo (intencionalmente limitado)
- Depende de IntelligenceService (pode ser gargalo)

### Otimizações Futuras

- [ ] Processar múltiplos alvos em paralelo
- [ ] Cachear resultados de validação (não revalidar)
- [ ] Implementar fallback de dados locais

---

## 🔗 Integração com Outros Componentes

### IntelligenceService
- **Relação:** Crítica (core da funcionalidade)
- **Dependência:** `await intelligence_service.research_and_validate()`
- **Impacto:** Se falhar, worker retorna erro

### AIProcessorWorker
- **Relação:** Complementar
- **Observação:** TargetResearchWorker valida alvos; AIProcessor analisa comentários

### MainRunner
- **Relação:** Supervisa
- **Observação:** MainRunner inicia TargetResearchWorker

---

## 📦 Dependências Externas

### Bibliotecas Python

| Biblioteca | Versão | Propósito |
|-----------|--------|----------|
| `asyncio` | Stdlib | Concorrência |
| `logging` | Stdlib | Logs |

### Serviços Externos

| Serviço | Criticidade |
|---------|-------------|
| **IntelligenceService** | CRÍTICA |
| **Supabase/PostgreSQL** | CRÍTICA |

---

## 📝 Changelog

### v84.16 (Junho 2026)
- ✅ Sistema de priorização (validação > utilidade)
- ✅ Modo "disabled/validation/utility"
- ✅ Integração com IntelligenceService
- ✅ Sistema de recompensa XP

---

**Documento Gerado:** Junho 2026  
**Status:** ✅ Completo
