# WkPesquisaAlvos — Curadoria e Inteligência de Alvos
_version: 90.8 | last_updated: 2026-06-07 | status: Ativo (Opcional, controlado por RESEARCHER_MODE)_

## 1. Visão Geral

**WkPesquisaAlvos** é o worker especializado em **validação de identidade** e **enriquecimento de metadados** para alvos (candidatos, políticos) monitorados na plataforma Sentinela. Foi migrado de `workers/ai/` para `workers/processors/` na Fase 9 para alinhamento de domínio.

### Informações Básicas
- **ID do Worker**: Dinâmico (e.g., `researcher-01`)
- **Localização**: `workers/processors/wk_pesquisa_alvos.py`
- **Classe**: `WkPesquisaAlvos` (herda de `BaseWorker`)
- **Serviço Core**: `core/intelligence_service.py`
- **Trigger**: Controlado por `RESEARCHER_MODE` — **desabilitado por padrão**
- **Status**: 🟡 Opcional

---

## 2. Responsabilidades

| Responsabilidade | Descrição |
|---|---|
| **Busca de Alvos Pendentes** | Procura candidatos com `status_monitoramento='Ativo'` e `identidade_validada=null` |
| **Validação de Identidade** | Executa `intelligence_service.research_and_validate()` para confirmar identidade |
| **Enriquecimento** | Atualiza metadados faltantes (bio, seguidores, etc) |
| **Priorização** | Ordena por `nota_relevancia` DESC para alvos mais importantes |
| **Cálculo de Qualidade** | Avalia qualidade da validação (0.0-1.0) |
| **Recompensa XP** | Distribui XP baseado em qualidade e sucesso |

---

## 3. Modos de Operação

### 1. "disabled" (Padrão)
```bash
RESEARCHER_MODE=disabled  # default — worker não executa
```
Worker retorna ciclo vazio (`error="disabled"`). **Este é o comportamento padrão em produção.**

### 2. "validation"
```bash
RESEARCHER_MODE=validation
```
Valida identidade de candidatos monitorados. Foca em alvos "Ativos" sem validação.

### 3. "utility"
```bash
RESEARCHER_MODE=utility
```
Enriquece dados de candidatos com bio vazia ou seguidores=0 (fallback quando fila de validação está vazia).

---

## 4. Execução

### Via Bandeja do Watchdog
```bash
python scripts/run_pesquisa_alvos.py
```
Menu: `WORKERS (WK)` → `WkPesquisaAlvos`

### Via Configuração
```python
# main_runner.py ou .env
RESEARCHER_MODE=validation  # ou 'utility'
```

---

## 5. Ciclo de Execução

```
setup() → cleanup_orphans()
run_cycle()
  1. Verifica RESEARCHER_MODE
  2. Busca alvo prioritário (identidade_validada IS NULL)
  3. Se vazio E mode='utility' → fallback para enriquecimento
  4. intelligence_service.research_and_validate(username)
  5. Cálculo de quality score → xp_delta
  6. CycleResult(target, xp_delta, quality)
teardown()
```

---

## 6. Monitoramento

```bash
tail -f logs/main_runner.json | grep "worker.researcher"
```

---

## 7. Troubleshooting

### "Worker retorna error='disabled'"
- É o comportamento **normal** em produção — `RESEARCHER_MODE=disabled` por padrão
- Para ativar: `export RESEARCHER_MODE=validation` ou `export RESEARCHER_MODE=utility`

### "no_tasks_available — nenhum alvo encontrado"
- Todos os alvos "Ativos" já foram validados — comportamento normal
- Ou não há candidatos com `status_monitoramento='Ativo'` no banco

---

## 8. Changelog

### v90.8 (2026-06-07)
- [x] Corrigido path: `workers/processors/wk_pesquisa_alvos.py`
- [x] Classe renomeada: `WkPesquisaAlvos`
- [x] Migrado de `workers/ai/` para `workers/processors/` (Fase 9)
- [x] Padrão `disabled` reforçado

---

**Última Revisão**: 2026-06-07
**PASA Version**: v84.16 → v90.8
