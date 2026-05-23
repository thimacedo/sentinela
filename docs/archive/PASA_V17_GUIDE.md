# 🥒 Guia Técnico: Arquitetura PASA v17 (Contracts & Events)

**Status**: 🚀 IMPLEMENTADO (Fase de Fundação e Core)
**Data**: 2026-05-14
**Versão**: v17.0.1 "The Intelligent Organism"

## 1. Visão Geral
A v17 abandona o modelo de "scripts isolados" em favor de uma arquitetura baseada em **Contratos de Dados** (Pydantic) e **Barramento de Eventos** (Event Bus sobre Postgres). O sistema agora é autossuficiente, auditável e resiliente.

## 2. Componentes Principais

### 🏗️ BaseWorker Pro (`workers/core/base_worker.py`)
O novo cérebro de todos os workers.
- **Retry Exponencial**: Tenta 3 vezes (2s, 4s, 8s) antes de falhar.
- **Ledger Histórico**: Registra cada execução na tabela `worker_runs`.
- **Auditoria de XP/Level**: Calcula performance e evolução do worker em tempo real.
- **Cleanup Seguro**: Garante que recursos (browser, conexões) sejam fechados via `finally`.

### 📡 Event Bus (`core/event_bus.py`)
Sistema de mensageria com concorrência segura.
- **Atômico**: Usa RPCs no Supabase com `FOR UPDATE SKIP LOCKED`.
- **Visibilidade**: Mensagens bloqueadas por 30s; se o worker morrer, ela volta para a fila.
- **Dead Letter Queue (DLQ)**: Mensagens que falham repetidamente são isoladas para investigação.

### 🧠 ClassifierWorker (`workers/processors/classifier_worker.py`)
- **Integração Gemini**: Consome a fila `classify_comments`.
- **Sanitização**: Limpa e valida respostas JSON da IA.
- **Persistência**: Atualiza `categoria_ia` e `is_hate` no banco de dados.

### 🚨 AlertWorker (`workers/processors/alert_worker.py`)
- **Detecção de Anomalias**: SQL Engine que identifica quedas de performance.
- **Notificações Push**: Integrado com Firebase (FCM) e Webhooks.
- **Resolução Automática**: Fecha alertas quando o sistema se normaliza.

## 3. O Fluxo de Dados (Life Cycle)
1. `InstagramWorker` raspa -> Valida via `CommentPayload` -> Salva -> Publica Evento.
2. `MainRunner` detecta evento -> Instancia `ClassifierWorker`.
3. `ClassifierWorker` -> Chama Gemini -> Persiste Classificação Real.
4. `AlertWorker` (cada 5min) -> Checa Saúde -> Notifica Admin se degradar.
5. `CleanupWorker` (cada 24h) -> Limpa logs antigos e DLQ.

## 🛠️ O que foi concluído (Done)
- [x] Migração SQL de Infraestrutura (Tabelas, Funções RPC, Views).
- [x] Schemas Pydantic com filtro anti-ruído de UI.
- [x] BaseWorker com Retries e Auditoria.
- [x] EventBus Atômico.
- [x] ClassifierWorker (Gemini 1.5).
- [x] MainRunner (Orquestrador).
- [x] AlertWorker + FCM Integration.
- [x] BaseScraper com Rotação de Sessão/Proxy.

## ⏳ Pendências e Próximos Passos (Backlog)
- [ ] **Migração de Workers Legados**: `CandidateScannerWorker`, `QueueManagerWorker` e `SearchWatcherWorker`.
- [ ] **Interface de Gestão de Contas**: Tela para cadastrar `scraping_accounts` via UI.
- [ ] **Refinamento de Prompts**: Ajustar o system prompt do Classifier para reduzir falsos positivos em NEUTRO.
- [ ] **Dashboard Real-Time**: Ligar os gráficos do front-end diretamente na view `worker_health`.

---
*Assinado: Pickle Rick 🥒 (O mestre dos commits)*
