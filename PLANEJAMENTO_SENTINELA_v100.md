# 📋 PLANEJAMENTO ESTRATÉGICO — SENTINELA v100+
## Arquitetura de Resiliência e Autonomia Operacional

**Data:** 2026-07-03
**Versão base:** v99.2
**Princípio orientador:** *Resiliência antes de velocidade. O sistema deve sobreviver a falhas silenciosas, mudanças de plataforma e indisponibilidade de serviços externos.*

---

## 🎯 Visão de Arquitetura Futura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SENTINELA — PLATAFORMA AUTÔNOMA v100+                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   COLETA     │  │  PROCESSAMENTO│  │   ANÁLISE    │  │   GOVERNANÇA │   │
│  │   (Agents)   │  │   (Workers)  │  │   (Skills)   │  │   (Cronjobs) │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │             │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐   │
│  │• IgCollector │  │• Classifier  │  │• SwarmDetect │  │• HealthCheck │   │
│  │• XCollector  │  │• Sentiment   │  │• NarrativeMap│  │• AutoHeal    │   │
│  │• TikCollector│  │• EntityLink  │  │• BotDetect   │  │• Repopulate  │   │
│  │• NewsScanner │  │• AutoLabel   │  │• TrendFore  │  │• BackupSync  │   │
│  │• SessionMgr  │  │• QueueDrain  │  │• ReportGen   │  │• AlertRouter │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    RESILIÊNCIA (Camada Transversal)                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │CircuitBrk│ │DeadLetter│ │Graceful  │ │Self-Heal │ │Observab. │   │   │
│  │  │  (CB)    │ │  (DLQ)   │ │Degradation│ │  (SH)   │ │ (O11y)   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 FASE 1 — AUTO-CURA E RESILIÊNCIA DE INFRAESTRUTURA
**Duração estimada:** 2-3 semanas
**Objetivo:** O sistema deve sobreviver a falhas de rede, banimentos de sessão, quedas de LLM e indisponibilidade do Supabase.

### 1.1 Agente: SentinelaSRE (Site Reliability Engineering)
**Tipo:** Agente autônomo contínuo (daemon)
**Responsabilidade:** Monitorar a saúde de todos os componentes e aplicar correções automáticas.

| Skill | Função | Gatilho |
|-------|--------|---------|
| `session_health_check` | Testa cada sessão IG a cada 15min | Cron 15min |
| `session_rotation` | Quando sessão banida, rotaciona para próxima | Evento: ban |
| `proxy_health_check` | Testa latência e disponibilidade de cada proxy | Cron 5min |
| `supabase_failover` | Se Supabase indisponível, opera em modo SQLite-only | Evento: timeout |
| `circuit_breaker_reset` | Monitora CB e força reset após cooldown + teste | Cron 10min |

### 1.2 Worker: WkSessaoAutonoma (Session Self-Healing)
**Arquivo:** `workers/sre/wk_sessao_autonoma.py`

Quando todas as sessões IG estiverem bloqueadas:
1. Tenta renovar cookies via login automatizado (playwright headless)
2. Se falhar, marca sessão como EXPIRADA e notifica operador
3. Se 2+ sessões EXPIRADA, entra em modo DEGRADED (coleta via DOM público sem login)

**Resiliência:** O sistema nunca para completamente. Degraded mode permite coleta limitada (posts públicos, sem comentários) até que sessões sejam renovadas.

### 1.3 Worker: WkDeadLetterQueue (DLQ Manager)
**Arquivo:** `workers/sre/wk_dead_letter_queue.py`

Capturar itens que falharam 3x consecutivas e:
- Salvar em `fila_dlq` (tabela Supabase) com stack trace, timestamp, versão do código
- Após 24h, tentar reprocessar automaticamente (pode ser bug transitório)
- Após 3 tentativas em DLQ, notifica operador via Ntfy com link para análise manual

**Schema DLQ:**
```sql
CREATE TABLE fila_dlq (
    id UUID PRIMARY KEY,
    original_target_id UUID,
    error_type VARCHAR(50),  -- 'extraction_failure', 'rate_limit', 'session_ban', 'llm_timeout'
    error_message TEXT,
    stack_trace TEXT,
    code_version VARCHAR(20),  -- 'v99.2'
    retry_count INT DEFAULT 0,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.4 Cronjob: cj_sre_health_check
**Frequência:** A cada 5 minutos
**Função:**
- Verificar heartbeat do agente autônomo (agent.status.json)
- Verificar locks órfãos na fila (> 30min)
- Verificar circuit breakers abertos há > 10min
- Verificar sessões bloqueadas há > 1h
- Se qualquer anomalia, aplicar auto-cura ou notificar

### 1.5 Cronjob: cj_sre_backup_sync
**Frequência:** A cada 30 minutos
**Função:**
- Sincronizar SQLite local → Supabase (bulk upsert com ignore_duplicates)
- Se Supabase indisponível, salvar em `data/backlog_sync.db` e tentar na próxima rodada
- Métrica: `sync_lag_seconds` — tempo desde o último comentário sincronizado

---

## 📌 FASE 2 — AUTOMAÇÃO DE COLETA MULTI-PLATAFORMA
**Duração estimada:** 3-4 semanas
**Objetivo:** Reduzir dependência única do Instagram. Coleta resilientemente de múltiplas fontes.

### 2.1 Agente: SentinelaCollector (Multi-Platform Collector)
**Tipo:** Agente de coleta unificado
**Responsabilidade:** Orquestrar coletores de diferentes plataformas com fallback entre eles.

| Plataforma | Worker | Estado | Fallback |
|------------|--------|--------|----------|
| Instagram | `WkColetaInstagram` | ✅ Existente | DOM público se API falhar |
| X/Twitter | `WkColetaX` | 🆕 Novo | Nitter/RSS se API rate limit |
| TikTok | `WkColetaTikTok` | 🆕 Novo | Scraping alternativo |
| Facebook | `WkColetaFacebook` | 🆕 Novo | Graph API limitada |
| Google News | `WkColetaNews` | 🆕 Novo | RSS + scraping |

**Arquitetura:** Cada worker implementa a mesma interface `BaseCollector`:
```python
class BaseCollector(ABC):
    async def collect(self, target: Target) -> CollectionResult
    async def health_check(self) -> HealthStatus
    async def degraded_mode(self) -> CollectionResult
```

### 2.2 Worker: WkColetaX (Twitter/X Collector)
**Arquivo:** `workers/scrapers/wk_coleta_x.py`

**Estratégia de resiliência:**
- **Camada 1:** API oficial (v2) com bearer token — mais rápida, mas rate limit agressivo
- **Camada 2:** Nitter instâncias (RSS/JSON) — sem autenticação, mas instâncias caem
- **Camada 3:** Scraping direto com Playwright — mais lento, mas resistente
- **Camada 4:** Google Cache / Wayback Machine — último recurso para posts antigos

**Circuit breaker separado por camada:** Se API cair, automaticamente tenta Nitter. Se Nitter cair, tenta scraping direto.

### 2.3 Worker: WkColetaNews (News Scanner)
**Arquivo:** `workers/scrapers/wk_coleta_news.py`

**Função:** Monitorar notícias sobre candidatos via Google News API, NewsAPI.org, RSS feeds de portais locais.

**Resiliência:** Se uma fonte não retorna notícias sobre o candidato em 7 dias, marca como `stale_source` e tenta outra.

### 2.4 Skill: PlatformRouter
**Arquivo:** `core/skills/platform_router.py`

**Função:** Decidir qual plataforma coletar baseado em:
- Disponibilidade de sessões/APIs
- Histórico de sucesso do alvo (ex: candidato mais ativo no X → prioriza X)
- Rate limits atuais
- Circuit breaker status

---

## 📌 FASE 3 — CLASSIFICAÇÃO AUTÔNOMA E CONTÍNUA
**Duração estimada:** 2-3 semanas
**Objetivo:** Pipeline de classificação que não depende de trigger manual. Classifica comentários assim que entram no buffer.

### 3.1 Agente: SentinelaClassifier (Classificador Autônomo)
**Tipo:** Agente contínuo (daemon separado ou thread no agente principal)
**Responsabilidade:** Consumir comentários não classificados da fila e aplicar classificação em cascata.

### 3.2 Worker: WkClassificaAutonomo (Auto-Classifier)
**Arquivo:** `workers/processors/wk_classifica_autonomo.py`

**Fluxo autônomo:**
```
Supabase (não classif) → FastDrop (triagem léxica) → LLM Cascade (classificação profunda)
         │                        │                        │
         ▼                        ▼                        ▼
   Batch 100 items          Descartar (não ódio)      Salvar (ódio/suspeito)
   a cada 30s
```

**Resiliência:**
- Se LLM cascade falha (todos modelos indisponíveis), salva em `comentarios_pendentes_llm` e tenta a cada 5 min
- Se FastDrop indica 100% não-ódio em um batch, pula LLM para economia (configurável)
- Métrica: `classification_lag_seconds` — tempo entre coleta e classificação

### 3.3 Worker: WkAutoLabel (Auto-Labeling de Contexto)
**Arquivo:** `workers/processors/wk_auto_label.py`

**Função:** Adicionar metadados automáticos aos comentários:
- **Tema:** Saúde, Educação, Segurança, Economia
- **Intenção:** Ataque pessoal, crítica política, desinformação, spam
- **Sentimento:** Positivo, negativo, neutro, sarcástico
- **Entidades:** Menciona outro candidato? Família? Partido?

**Resiliência:** Labels são soft — se falha, o comentário ainda é classificado como ódio/não-ódio. Labels são `NULL` e podem ser preenchidas depois.

### 3.4 Cronjob: cj_classifier_drain
**Frequência:** A cada 60 segundos
**Função:** Buscar comentários não classificados (limit 100), aplicar FastDrop em batch, aplicar LLM cascade nos que passaram, upsert resultados. Se backlog > 1000, notifica operador.

### 3.5 Skill: ModelVersionManager
**Arquivo:** `core/skills/model_version_manager.py`

**Função:** Gerenciar versões de modelos de classificação:
- A/B test entre modelos (ex: Sabia-4 vs Mistral Large)
- Rollback automático se taxa de classificação anômala (ex: 90% ódio quando normal é 15%)
- Métricas de qualidade: precision, recall, F1 calculados via amostra humana periódica

---

## 📌 FASE 4 — INTELIGÊNCIA E ANÁLISE PREDITIVA
**Duração estimada:** 3-4 semanas
**Objetivo:** Transformar dados coletados em inteligência acionável automaticamente.

### 4.1 Agente: SentinelaIntelligence (Inteligência Preditiva)
**Tipo:** Agente de análise contínua
**Responsabilidade:** Detectar padrões, swarms, campanhas coordenadas e gerar alertas.

### 4.2 Worker: WkSwarmDetector (Detecção de Swarms — Solenya v2)
**Arquivo:** `workers/analytics/wk_swarm_detector_v2.py`

**Melhorias sobre Solenya v99.2:**
- **Temporal clustering:** Detectar swarms que duram > 24h (campanhas coordenadas)
- **Cross-platform:** Correlacionar swarms entre Instagram e X
- **Bot scoring:** Score de 0-100 para cada conta participante baseado em padrões de comportamento
- **Narrative drift:** Detectar quando a narrativa de um swarm muda (ex: de 'corrupção' para 'saúde mental')

**Resiliência:** Se LLM falha na inferência cognitiva, fallback para análise estatística pura (TF-IDF + clustering clássico).

### 4.3 Worker: WkTrendForecaster (Previsão de Tendências)
**Arquivo:** `workers/analytics/wk_trend_forecaster.py`

**Função:**
- Prever volume de discurso de ódio para os próximos 7 dias por candidato
- Detectar 'early signals' — aumento de 300% em menções negativas em 6h
- Alertar quando um candidato está prestes a virar alvo de campanha coordenada

**Resiliência:** Modelo estatístico simples (ARIMA/Prophet) como fallback se LLM indisponível.

### 4.4 Worker: WkReportGenerator (Geração Autônoma de Relatórios)
**Arquivo:** `workers/analytics/wk_report_generator.py`

**Função:** Gerar relatórios diários/semanais automaticamente em Markdown/PDF, enviar para stakeholders via email/Ntfy.

**Resiliência:** Se geração de PDF falha, envia Markdown puro. Se email falha, envia Ntfy.

### 4.5 Cronjob: cj_intelligence_sweep
**Frequência:** A cada 6 horas
**Função:** Executar WkSwarmDetector em todos os candidatos ATIVOS, executar WkTrendForecaster, se swarm crítico detectado (> 50 contas, > 1000 comentários, bot_score > 70): gerar alerta Ntfy PRIORITY 5 e acionar WkReportGenerator com foco no swarm.

---

## 📌 FASE 5 — GOVERNANÇA, AUDITORIA E CONFORMIDADE
**Duração estimada:** 2 semanas
**Objetivo:** Garantir que o sistema opere dentro de limites éticos e legais, com audit trail completo.

### 5.1 Agente: SentinelaGovernance (Governança e Auditoria)
**Tipo:** Agente de auditoria contínua
**Responsabilidade:** Garantir conformidade, limites de coleta, e audit trail.

### 5.2 Worker: WkAuditoriaEtica (Auditoria Ética)
**Arquivo:** `workers/governance/wk_auditoria_etica.py`

**Função:**
- Verificar se coleta respeita limites configurados (max_posts, max_comments, max_age_days)
- Detectar over-collection (coleta de posts privados, perfis de menores, dados sensíveis)
- Gerar log de auditoria imutável (hash chain) para cada ação do sistema
- Apagar automaticamente dados além do período de retenção configurado (LGPD/GDPR)

### 5.3 Worker: WkBiasDetector (Detecção de Viés)
**Arquivo:** `workers/governance/wk_bias_detector.py`

**Função:** Monitorar se o sistema está coletando/classificando de forma equilibrada entre espectro político. Detectar viés de seleção (ex: 90% dos alvos são de um único partido). Alertar curador se viés detectado.

### 5.4 Cronjob: cj_governance_audit
**Frequência:** Diário (02:00)
**Função:** Verificar retenção de dados, verificar balanceamento de coleta por partido/ideologia, gerar relatório de auditoria em audit_log. Se anomalia ética, notifica operador e pausa coleta do alvo afetado.

---

## 📌 FASE 6 — ESCALONAMENTO E PERFORMANCE
**Duração estimada:** 2-3 semanas
**Objetivo:** Permitir que o sistema escale sem perder resiliência. Não é sobre velocidade, mas sobre capacidade de processar mais alvos sem quebrar.

### 6.1 Worker: WkShardManager (Gerenciador de Shards)
**Arquivo:** `workers/sre/wk_shard_manager.py`

**Função:** Dividir candidatos em shards (ex: shard 1 = candidatos A-M, shard 2 = N-Z). Distribuir shards entre múltiplas instâncias do agente autônomo. Garantir que cada candidato seja processado por exatamente uma instância (coordenação via Supabase).

### 6.2 Worker: WkLoadBalancer (Balanceador de Carga)
**Arquivo:** `workers/sre/wk_load_balancer.py`

**Função:** Monitorar carga de cada worker (coleta, classificação, análise). Se um worker está com backlog > 1000 itens, spawnar worker adicional (se recursos disponíveis). Se worker inativo por > 10 min, desalocar recursos.

### 6.3 Cronjob: cj_performance_tuning
**Frequência:** A cada 30 minutos
**Função:** Medir latência média de coleta por plataforma, medir latência média de classificação por LLM. Se latência de coleta > 5 min/post, reduzir max_posts ou aumentar workers. Se latência de classificação > 30s/comentário, ativar FastDrop mais agressivo. Ajustar dinamicamente: max_posts, max_comments, batch_size.

---

## 📊 CRONJOBS CONSOLIDADOS

| Cronjob | Frequência | Fase | Responsabilidade |
|---------|-----------|------|------------------|
| `cj_sre_health_check` | 5 min | 1 | Verificar saúde de todos os componentes |
| `cj_sre_backup_sync` | 30 min | 1 | Sincronizar SQLite ↔ Supabase |
| `cj_classifier_drain` | 60 seg | 3 | Consumir backlog de comentários não classificados |
| `cj_intelligence_sweep` | 6 horas | 4 | Detectar swarms, tendências, gerar alertas |
| `cj_governance_audit` | Diário 02:00 | 5 | Auditoria ética, retenção, viés |
| `cj_performance_tuning` | 30 min | 6 | Ajustar parâmetros dinamicamente |
| `cj_session_refresh` | 15 min | 1 | Testar e renovar sessões IG |
| `cj_proxy_rotation` | 10 min | 1 | Testar latência e rotacionar proxies |
| `cj_ntfy_digest` | 6 horas | 4 | Enviar digest de métricas para stakeholders |

---

## 🛠️ SKILLS (Biblioteca de Capacidades Reutilizáveis)

| Skill | Arquivo | Função |
|-------|---------|--------|
| `CircuitBreaker` | `core/skills/circuit_breaker.py` | Isolar falhas, cooldown progressivo |
| `DeadLetterQueue` | `core/skills/dead_letter_queue.py` | Capturar e reprocessar falhas |
| `GracefulDegradation` | `core/skills/graceful_degradation.py` | Modo degradado quando serviço indisponível |
| `SelfHeal` | `core/skills/self_heal.py` | Auto-cura de sessões, proxies, seletores |
| `Observability` | `core/skills/observability.py` | Métricas, logs estruturados, tracing |
| `PlatformRouter` | `core/skills/platform_router.py` | Escolher plataforma ótima por alvo |
| `ModelVersionManager` | `core/skills/model_version_manager.py` | A/B test, rollback de modelos LLM |
| `RateLimitAdapter` | `core/skills/rate_limit_adapter.py` | Adaptar velocidade conforme rate limits |
| `SessionPool` | `core/skills/session_pool.py` | Gerenciar pool de sessões com health check |
| `ProxyPool` | `core/skills/proxy_pool.py` | Gerenciar pool de proxies com latência |
| `NtfyRouter` | `core/skills/ntfy_router.py` | Roteamento inteligente de notificações |
| `AuditTrail` | `core/skills/audit_trail.py` | Hash chain de auditoria imutável |

---

## 📈 MÉTRICAS DE RESILIÊNCIA (KPIs)

| Métrica | Target | Alerta |
|---------|--------|--------|
| `system_uptime_pct` | > 99.5% | < 99% |
| `coleta_success_rate` | > 95% | < 90% |
| `classification_lag_sec` | < 300s | > 600s |
| `dlq_size` | < 50 | > 100 |
| `session_availability` | > 2/3 ativas | < 1/3 ativas |
| `sync_lag_sec` | < 1800s | > 3600s |
| `swarm_detection_lag_h` | < 6h | > 12h |
| `classification_accuracy` | > 85% F1 | < 80% F1 |
| `bias_score` | < 0.2 (equilibrado) | > 0.3 |

---

## 🗓️ ROADMAP SUGERIDO

```
Semana 1-2:   FASE 1 — SRE, DLQ, Session Self-Healing, Backup Sync
Semana 3-4:   FASE 2 — X Collector, News Scanner, Platform Router
Semana 5-6:   FASE 3 — Auto-Classifier, Auto-Label, Model Version Manager
Semana 7-8:   FASE 4 — Swarm Detector v2, Trend Forecaster, Report Generator
Semana 9-10:  FASE 5 — Auditoria Ética, Bias Detector, Audit Trail
Semana 11-12: FASE 6 — Shard Manager, Load Balancer, Performance Tuning
```

**Observação:** Cada fase pode ser entregue independentemente. O sistema continua operando durante as transições. Nenhuma fase quebra retrocompatibilidade.

---

## 🎯 Princípios de Design

1. **Resiliência > Velocidade:** Um sistema lento que funciona é melhor que um rápido que quebra.
2. **Graceful Degradation:** Se um componente falha, o resto continua. Nunca falha em cascata.
3. **Observabilidade:** Toda ação deve ser observável (log, métrica, trace). Falhas silenciosas são inaceitáveis.
4. **Autonomia Gradual:** Começar com assistência humana (HITL) e remover conforme confiança aumenta.
5. **Ética por Design:** Auditoria, viés e privacidade são features, não afterthoughts.
6. **Fallbacks em Cascata:** Sempre ter 3 camadas: ótima, aceitável, mínima viável.
7. **Idempotência:** Toda operação pode ser repetida sem efeitos colaterais.

---

*Documento gerado em 2026-07-03 para o projeto Sentinela.*
*Versão base: v99.2 | Estado: 100% operacional | Próximo marco: v100.0 (SRE completo)*