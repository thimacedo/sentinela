# ARQUITETURA TÉCNICA: SENTINELA v86.0 (Intelligence Governance)
_last_updated: 2026-05-29 | Protocolo PASA Ativo_

## 1. Visão Geral do Ecossistema
O Sentinela v86.0 evoluiu de um simples scraper para uma **Malha de Inteligência Governança (Intelligence Mesh)**. O sistema agora é composto por cinco camadas interdependentes que garantem furtividade, economia e precisão técnica.

---

## 2. Camadas de Operação

### 🛡️ Camada 1: Coleta Furtiva (Stealth Scraping)
- **Motor**: `InstagramScraperV2` baseado em Playwright.
- **Diferencial**: Implementa **Stealth Mode v85.10**.
  - Rotação dinâmica de fingerprints (Windows, Mac, iPhone, Android).
  - Viewports e User-Agents aleatórios por ciclo.
  - Emulação de comportamento humano (Jitter e Mouse movement).
  - Bypass de detecção de automação via injeção de scripts.

### 🧠 Camada 2: Inteligência Híbrida (Hybrid AI Triage)
- **Motor**: `AIService` com cascata de triagem.
- **Processo**:
  1. **Triagem Local (Ollama)**: Filtra ~60% do tráfego (Lixo/Neutro) a custo zero.
  2. **Perícia Cloud (Mistral/Groq)**: Realiza análise profunda (MCA v2.2) apenas em dados suspeitos.
  3. **Auto-Refinamento**: No tempo ocioso, o sistema re-analisa registros de baixa confiança utilizando modelos de alta fidelidade.

### 🕸️ Camada 3: Analytics e Redes (Coordination Detection)
- **Motor**: `NetworkMinerWorker` utilizando NetworkX.
- **Função**: Identifica clusters de ataque e comunidades coordenadas.
- **Output**: Grafos de influência exibidos na página `/rede`, destacando contas multi-target e táticas de bot-nets.

### 📄 Camada 4: Produtos Forenses (Dossier Production)
- **Serviço**: `DossieService` via `fpdf2`.
- **Integridade**: Cada PDF gerado possui uma assinatura digital **SHA-256**, vinculando os dados à data de extração para validade técnica.
- **Conteúdo**: Resumo executivo, score de severidade e breakdown das 50 evidências mais críticas.

### 💰 Camada 5: Governança Financeira (CI Ledger)
- **Motor**: `TreasurerWorker`.
- **Moeda**: **Créditos de Inteligência (CI)**.
- **Responsabilidade**: 
  - Auditoria de saldos negativos.
  - Conciliação Stripe vs Supabase.
  - Monitoramento de Burn Rate (Custo de IA/Proxy).
  - Geração de DRE Diário de Operações.

---

## 🏗️ 3. Fluxo de Dados (Data Pipeline)

1.  **Ingestão**: `InstagramWorker` captura comentários ➔ Salva em `comentarios` (`processado_ia = false`).
2.  **Triagem**: `AIProcessor` consome o lote ➔ Chama Ollama ➔ (Se necessário) Chama Cloud ➔ Salva classificação.
3.  **Mineração**: `NetworkMiner` analisa o banco ➔ Gera clusters ➔ Salva em `redes_coordenadas`.
4.  **Entrega**: Usuário solicita Dossiê ➔ `Treasurer` valida saldo (-350 CI) ➔ `DossieService` gera PDF ➔ Registro salvo em `dossies`.

---

## 📊 4. KPIs de Performance (v86.0)
- **Latência de Perícia**: < 2.5s por lote.
- **Eficiência Financeira**: Economia de 55% em APIs Cloud via Triage Local.
- **Furtividade**: Longevidade de sessões aumentada em 3x após Stealth Mode.

---
_Este documento é a base para o desenvolvimento das Fases 7 e 8 do ROADMAP._
