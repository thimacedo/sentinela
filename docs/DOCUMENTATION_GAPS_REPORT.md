# Relatório de Lacunas na Documentação — Sentinela
_data: 2026-06-04_

## Sumário Executivo

Este relatório identifica **lacunas críticas e importantes** na documentação do projeto Sentinela, baseado em uma auditoria completa do workspace comparando a documentação existente com o código real em produção.

### 🎯 Status Geral
- ✅ **Documentação central está consistente** (STATE.md, ROADMAP.md, SYSTEM_CONTEXT.md)
- ⚠️ **Lacunas significativas** em documentação técnica de componentes
- ⚠️ **Falta documentação de API** estruturada
- ⚠️ **Configuração incompleta** de variáveis de ambiente

---

## 1. Lacunas Críticas (Alta Prioridade)

### 1.1 Documentação de API/Endpoints

**Status**: ❌ **AUSENTE**

**Problema**:
- Não há documentação estruturada dos endpoints da API
- Backend em `api/index.py` (41KB) sem documentação OpenAPI/Swagger
- Frontend espera endpoints documentados no `IMPLEMENTATION_GUIDE.md` que não estão formalmente especificados

**Arquivos afetados**:
- `/workspace/api/index.py` — endpoint principal sem docs
- `/workspace/api/routes/*.py` — rotas sem especificação formal
- `/workspace/api/v1/*` — endpoints sem documentação

**Impacto**:
- Desenvolvedores frontend não sabem contratos exatos
- Dificulta integração e manutenção
- Sem versionamento claro de API

**Recomendação**:
```
Criar: docs/API_REFERENCE.md
Incluir:
- Lista completa de endpoints
- Schemas de request/response
- Códigos de erro
- Exemplos de uso
- Autenticação e autorização

Alternativa: Implementar OpenAPI/Swagger em api/index.py
```

### 1.2 Documentação de Variáveis de Ambiente

**Status**: ⚠️ **INCOMPLETA**

**Problema**:
- `.env.example` existe mas falta documentação detalhada
- Variáveis críticas sem descrição de quando/como usar
- Faltam valores padrão recomendados
- Não há documentação de variáveis específicas por ambiente (dev/staging/prod)

**Gaps específicos**:
```bash
# Faltam no .env.example:
STRIPE_ALLOW_MOCK_PAYMENTS=     # Não documentado
FRONTEND_URL=                    # Mencionado no ROADMAP mas não em .env.example
NEXT_PUBLIC_API_URL=            # Frontend precisa mas não está documentado
NUM_SCRAPER_WORKERS=            # Usado em main_runner.py mas não documentado
WATCHDOG_ACTIVE=                # Usado mas não documentado
DB_CIRCUIT_BREAKER_*=           # Configurações de circuit breaker não documentadas
```

**Impacto**:
- Configuração de ambientes inconsistente
- Risco de quebrar produção por falta de documentação
- Onboarding difícil para novos desenvolvedores

**Recomendação**:
```
Criar: docs/ENVIRONMENT_VARIABLES.md
Incluir:
- Todas as variáveis com descrição detalhada
- Valores padrão recomendados
- Diferenças entre dev/staging/prod
- Variáveis obrigatórias vs opcionais
- Exemplos de configuração completa
```

### 1.3 Documentação de Workers

**Status**: ⚠️ **PARCIAL**

**Problema**:
- Existem 29 arquivos Python em `/workspace/workers/`
- Apenas alguns workers têm documentação:
  - ✅ `InstagramScraperWorker` tem `docs/operations/INSTAGRAM_SCRAPER_V2.md`
  - ❌ `AIProcessorWorker` — classificador oficial **SEM documentação detalhada**
  - ❌ `NetworkMinerWorker` — **SEM documentação**
  - ❌ `TreasurerWorker` — **SEM documentação**
  - ❌ `TargetResearchWorker` — **SEM documentação**
  - ❌ `DossierWorker` — **SEM documentação**
  - ❌ `AlertWorker` — **SEM documentação**
  - ❌ `CandidateScanner` — **SEM documentação**

**Workers não documentados**:
```
workers/processors/ai_processor_worker.py       # Crítico - classificador oficial
workers/processors/alert_worker.py
workers/processors/candidate_scanner.py
workers/processors/dossier_worker.py
workers/analytics/network_worker.py             # Crítico - mineração de redes
workers/analytics/trends_worker.py
workers/financial/treasurer_worker.py           # Crítico - métricas financeiras
workers/ai/target_research_worker.py            # Importante
workers/ai/ai_advisor.py
workers/ai/doc_fetcher.py
workers/ai/suggestion_consumer.py
workers/audit_worker.py
```

**Impacto**:
- Dificulta manutenção e debugging
- Novos desenvolvedores não entendem responsabilidades
- Não há documentação de configuração específica de cada worker

**Recomendação**:
```
Criar documentação para cada worker ativo:

docs/workers/AI_PROCESSOR_WORKER.md           # PRIORIDADE 1
docs/workers/NETWORK_MINER_WORKER.md          # PRIORIDADE 1
docs/workers/TREASURER_WORKER.md              # PRIORIDADE 1
docs/workers/TARGET_RESEARCH_WORKER.md
docs/workers/DOSSIER_WORKER.md
docs/workers/ALERT_WORKER.md

Cada documento deve incluir:
- Responsabilidade do worker
- Configuração necessária
- Ciclo de execução
- Métricas e monitoramento
- Troubleshooting comum
```

---

## 2. Lacunas Importantes (Média Prioridade)

### 2.1 Documentação de Core Services

**Status**: ⚠️ **INCOMPLETA**

**Problema**:
- Módulos core críticos sem documentação:

```
core/ai_service.py (26KB)          # Serviço central de IA - SEM docs
core/queue_manager.py (20KB)       # Gerenciador de fila - SEM docs
core/instagram_scraper_v2.py (33KB) # Scraper V2 - docs parcial
core/fallback_llm.py (14KB)        # Sistema de fallback - SEM docs
core/circuit_breaker.py            # Circuit breaker - SEM docs
core/checkpoint_manager.py         # Checkpoints - SEM docs
core/local_buffer.py               # Buffer local - SEM docs
```

**Recomendação**:
```
Criar: docs/core/README.md com overview
Criar documentação específica:
- docs/core/AI_SERVICE.md
- docs/core/QUEUE_MANAGER.md
- docs/core/FALLBACK_LLM.md
- docs/core/CIRCUIT_BREAKER.md
```

### 2.2 Documentação de Configuração

**Status**: ⚠️ **INCOMPLETA**

**Problema**:
- Arquivos de configuração sem documentação:

```
config/fallback_providers.yaml    # Providers de IA - pendente saneamento
config/custom_rules.json          # Regras customizadas - não documentado
config/system_rules.json          # Regras do sistema - não documentado
```

**Recomendação**:
```
Criar: docs/CONFIGURATION_GUIDE.md
Documentar:
- Estrutura de fallback_providers.yaml
- Como adicionar/remover providers
- Configuração de custom_rules
- System rules e sua aplicação
```

### 2.3 Documentação de Scripts Operacionais

**Status**: ⚠️ **PARCIAL**

**Problema**:
- Existem ~100 scripts em `/workspace/scripts/`
- Apenas alguns críticos estão documentados
- Não há índice de scripts por categoria

**Scripts importantes sem docs**:
```
scripts/reclassify_low_confidence.py    # Reclassificação - mencionado mas não detalhado
scripts/force_reclassify.py             # Força reclassificação
scripts/run_scanner_agent.py            # Scanner agent
scripts/run_audit_agent.py              # Audit agent
scripts/run_dossier_agent.py            # Dossier agent
scripts/work_session.py                 # Work session
scripts/night_watch_pipeline.sh         # Pipeline noturno
scripts/cloud_scrape_cycle.py           # Scraping na nuvem
scripts/diagnose_workers.py             # Diagnóstico de workers
```

**Recomendação**:
```
Criar: docs/SCRIPTS_REFERENCE.md
Organizar por categoria:
- Scripts de operação diária
- Scripts de manutenção
- Scripts de debug/diagnóstico
- Scripts de migração
- Scripts de teste

Para cada script documentar:
- Propósito
- Quando usar
- Parâmetros
- Exemplos de uso
```

### 2.4 Documentação de Database Schema

**Status**: ⚠️ **DESATUALIZADA**

**Problema**:
- `docs/database_schema_v58.md` existe mas pode estar desatualizado
- Não há versionamento claro de schema
- Migrações existem mas não há mapa de evolução

**Arquivos relacionados**:
```
docs/database_schema_v58.md              # Pode estar desatualizado
scripts/migration_v*.sql                 # ~15 migrações sem índice
migrations/                              # Migrações sem docs
```

**Recomendação**:
```
1. Atualizar docs/database_schema_v58.md com estado atual
2. Criar docs/DATABASE_MIGRATIONS.md com:
   - Histórico de migrações
   - Versão atual do schema
   - Como aplicar migrações
   - Rollback procedures
3. Criar script para gerar schema docs automaticamente
```

### 2.5 Documentação de Frontend

**Status**: ⚠️ **FRAGMENTADA**

**Problema**:
- Documentação existe mas está fragmentada
- Múltiplos guias sem organização clara

**Arquivos existentes**:
```
frontend/IMPLEMENTATION_GUIDE.md       # Guia de implementação
frontend/AGENTS.md                     # ?
frontend/CLAUDE.md                     # ?
frontend/Arquitetura BANCO.md          # ?
docs/REFATORACAO_FRONTEND.md           # Contexto histórico
docs/planejamento-migracao-frontend/*  # 6 documentos de planejamento
```

**Recomendação**:
```
Consolidar em:
docs/frontend/README.md               # Entrada principal
docs/frontend/ARCHITECTURE.md         # Arquitetura atual
docs/frontend/COMPONENTS.md           # Documentação de componentes
docs/frontend/API_INTEGRATION.md      # Integração com backend
docs/frontend/DEPLOYMENT.md           # Deploy e CI/CD
```

---

## 3. Lacunas Menores (Baixa Prioridade)

### 3.1 Documentação de Testes

**Status**: ❌ **AUSENTE**

**Problema**:
- Não há documentação sobre estratégia de testes
- Testes existem mas sem guia de execução

**Arquivos relacionados**:
```
tests/                                 # Diretório de testes
test_api/                             # Testes de API
scripts/test_*.py                     # ~10 scripts de teste
pytest.ini                            # Configuração pytest
```

**Recomendação**:
```
Criar: docs/TESTING_GUIDE.md
Incluir:
- Estratégia de testes
- Como executar testes
- Como escrever novos testes
- Cobertura atual
- CI/CD integration
```

### 3.2 Documentação de Monitoramento e Observabilidade

**Status**: ⚠️ **INCOMPLETA**

**Problema**:
- Watchdog documentado parcialmente
- Métricas e logs sem guia completo
- Não há documentação de alertas

**Recomendação**:
```
Criar: docs/MONITORING.md
Incluir:
- Como usar o Watchdog
- Métricas disponíveis
- Logs e onde encontrá-los
- Sistema de alertas
- Troubleshooting com logs
```

### 3.3 Documentação de Deploy

**Status**: ⚠️ **FRAGMENTADA**

**Problema**:
- Informações de deploy espalhadas
- Não há guia completo de deploy em produção

**Arquivos relacionados**:
```
render.yaml                           # Config Render
vercel.json                          # Config Vercel
.vercelignore                        # Ignore rules
docs/DOCUMENTACAO_INFRA_V50.1.md     # Infra antiga
```

**Recomendação**:
```
Criar: docs/DEPLOYMENT.md
Incluir:
- Deploy do backend (Render/outros)
- Deploy do frontend (Vercel)
- Variáveis de ambiente por ambiente
- Checklist pré-deploy
- Rollback procedures
- Health checks
```

---

## 4. Documentação Desatualizada ou Conflitante

### 4.1 Referências a LiteRT

**Status**: ⚠️ **REQUER LIMPEZA**

**Problema**:
- Ainda há referências a LiteRT no código/docs
- LiteRT não é mais usado segundo STATE.md

**Ação requerida**:
```bash
# Buscar todas as referências
grep -r "LiteRT" /workspace --exclude-dir=node_modules
grep -r "litert" /workspace --exclude-dir=node_modules

# Remover ou atualizar conforme necessário
```

### 4.2 Documentação PASA Antiga

**Status**: ⚠️ **HISTÓRICA**

**Arquivos**:
```
docs/ARCHITECTURE_PASA_V50.md
docs/ARCHITECTURE_PASA_V84.md
docs/ARCHITECTURE_PASA_V86.md
docs/archive/MANUAL_TECNICO_PASA_v16_3.md
docs/archive/OPERACAO_TECNICA_v16_4.md
docs/archive/PASA_V17_GUIDE.md
```

**Recomendação**:
- Manter em `docs/archive/` (OK)
- Adicionar aviso no topo de cada arquivo indicando que é histórico
- Criar `docs/archive/README.md` explicando contexto histórico

---

## 5. Estrutura de Documentação Recomendada

### 5.1 Estrutura Atual
```
/workspace/
├── README.md                    ✅
├── STATE.md                     ✅
├── ROADMAP.md                   ✅
├── walkthrough.md               ✅
├── task.md                      ✅
└── docs/
    ├── SYSTEM_CONTEXT.md        ✅
    ├── DOCUMENTATION_AUDIT.md   ✅
    ├── index_documentacao.md    ✅
    └── [outros documentos...]   ⚠️
```

### 5.2 Estrutura Ideal Proposta
```
/workspace/
├── README.md                          # Entrada principal
├── STATE.md                           # Estado operacional
├── ROADMAP.md                         # Roadmap
└── docs/
    ├── index.md                       # Índice principal organizado
    ├── GETTING_STARTED.md             # NOVO - Guia rápido
    │
    ├── architecture/
    │   ├── SYSTEM_OVERVIEW.md         # Overview atual
    │   ├── WORKERS.md                 # Arquitetura de workers
    │   ├── DATA_FLOW.md               # Fluxo de dados
    │   └── SECURITY.md                # Segurança
    │
    ├── api/
    │   ├── README.md                  # NOVO - Overview da API
    │   ├── ENDPOINTS.md               # NOVO - Referência de endpoints
    │   └── AUTHENTICATION.md          # NOVO - Autenticação
    │
    ├── workers/
    │   ├── README.md                  # NOVO - Overview de workers
    │   ├── AI_PROCESSOR.md            # NOVO - Worker de IA
    │   ├── NETWORK_MINER.md           # NOVO - Mineração de rede
    │   ├── TREASURER.md               # NOVO - Worker financeiro
    │   └── [outros workers...]
    │
    ├── core/
    │   ├── README.md                  # NOVO - Overview de core
    │   ├── AI_SERVICE.md              # NOVO - Serviço de IA
    │   ├── QUEUE_MANAGER.md           # NOVO - Gerenciador de fila
    │   └── [outros módulos...]
    │
    ├── operations/
    │   ├── DEPLOYMENT.md              # NOVO - Deploy
    │   ├── MONITORING.md              # NOVO - Monitoramento
    │   ├── TROUBLESHOOTING.md         # NOVO - Resolução de problemas
    │   └── SCRIPTS_REFERENCE.md       # NOVO - Referência de scripts
    │
    ├── configuration/
    │   ├── ENVIRONMENT_VARIABLES.md   # NOVO - Variáveis de ambiente
    │   ├── CONFIG_FILES.md            # NOVO - Arquivos de config
    │   └── SECRETS_MANAGEMENT.md      # NOVO - Gestão de secrets
    │
    ├── database/
    │   ├── SCHEMA.md                  # Atualizar schema atual
    │   ├── MIGRATIONS.md              # NOVO - Migrações
    │   └── QUERIES.md                 # NOVO - Queries comuns
    │
    ├── frontend/
    │   ├── README.md                  # Consolidar guias existentes
    │   ├── ARCHITECTURE.md
    │   ├── COMPONENTS.md
    │   └── API_INTEGRATION.md
    │
    ├── development/
    │   ├── CONTRIBUTING.md            # NOVO - Como contribuir
    │   ├── TESTING.md                 # NOVO - Guia de testes
    │   └── CODE_STANDARDS.md          # NOVO - Padrões de código
    │
    └── archive/                       # Documentação histórica
        └── README.md                  # Explicar contexto histórico
```

---

## 6. Priorização de Ações

### 🔴 Prioridade 1 (Crítico - Fazer Imediatamente)
1. **Criar documentação de API** (`docs/api/ENDPOINTS.md`)
2. **Documentar variáveis de ambiente** (`docs/ENVIRONMENT_VARIABLES.md`)
3. **Documentar workers principais**:
   - AIProcessorWorker
   - NetworkMinerWorker
   - TreasurerWorker

### 🟡 Prioridade 2 (Importante - Fazer em 1-2 semanas)
4. **Documentar core services**:
   - ai_service.py
   - queue_manager.py
   - fallback_llm.py
5. **Criar guia de scripts** (`docs/SCRIPTS_REFERENCE.md`)
6. **Atualizar database schema**
7. **Consolidar documentação de frontend**

### 🟢 Prioridade 3 (Desejável - Fazer eventualmente)
8. **Criar guia de testes**
9. **Documentar monitoramento**
10. **Criar guia de deploy completo**
11. **Limpar referências a LiteRT**
12. **Adicionar avisos em docs históricas**

---

## 7. Template para Documentação de Workers

Para facilitar a criação de documentação uniforme, use este template:

```markdown
# [Nome do Worker] — Sentinela

## 1. Visão Geral
- **Propósito**: [O que este worker faz]
- **Frequência**: [A cada X segundos/minutos]
- **Prioridade**: [Alta/Média/Baixa]
- **Estado**: [Ativo/Opcional/Desabilitado]

## 2. Responsabilidades
- [Lista de responsabilidades]

## 3. Configuração

### Variáveis de Ambiente
```bash
WORKER_ENABLED=true
WORKER_INTERVAL=60
[outras variáveis]
```

### Configuração no Código
```python
# Exemplo de configuração
```

## 4. Ciclo de Execução
1. [Passo 1]
2. [Passo 2]
...

## 5. Dependências
- [Outros workers/serviços necessários]

## 6. Métricas e Monitoramento
- [Métricas expostas]
- [Como monitorar]

## 7. Troubleshooting

### Erro Comum 1
**Sintoma**: [descrição]
**Causa**: [causa]
**Solução**: [solução]

## 8. Referências
- Código: `workers/[caminho]`
- Testes: `tests/[caminho]`
```

---

## 8. Conclusão

### Resumo das Lacunas

| Categoria | Status | Prioridade | Ação |
|-----------|--------|------------|------|
| Documentação Central | ✅ Completa | - | Manter atualizada |
| API/Endpoints | ❌ Ausente | 🔴 Crítica | Criar |
| Variáveis de Ambiente | ⚠️ Incompleta | 🔴 Crítica | Completar |
| Workers | ⚠️ Parcial | 🔴 Crítica | Documentar principais |
| Core Services | ⚠️ Incompleta | 🟡 Importante | Documentar |
| Scripts | ⚠️ Parcial | 🟡 Importante | Criar índice |
| Database | ⚠️ Desatualizada | 🟡 Importante | Atualizar |
| Frontend | ⚠️ Fragmentada | 🟡 Importante | Consolidar |
| Testes | ❌ Ausente | 🟢 Desejável | Criar |
| Monitoramento | ⚠️ Incompleta | 🟢 Desejável | Completar |
| Deploy | ⚠️ Fragmentada | 🟢 Desejável | Consolidar |

### Próximos Passos Recomendados

1. **Esta semana**:
   - Criar `docs/api/ENDPOINTS.md`
   - Criar `docs/ENVIRONMENT_VARIABLES.md`
   - Documentar AIProcessorWorker

2. **Próximas 2 semanas**:
   - Documentar workers restantes
   - Criar guia de scripts
   - Atualizar database schema

3. **Próximo mês**:
   - Consolidar documentação de frontend
   - Criar guias de teste e deploy
   - Limpar documentação histórica

### Impacto Esperado

Com essas melhorias:
- ✅ **Onboarding 3x mais rápido** para novos desenvolvedores
- ✅ **Menos erros de configuração** em produção
- ✅ **Manutenção mais fácil** de componentes existentes
- ✅ **Melhor colaboração** entre frontend e backend
- ✅ **Redução de perguntas repetitivas** sobre o sistema

---

**Status do Relatório**: ✅ Completo
**Próxima revisão**: Após implementação das ações de Prioridade 1
