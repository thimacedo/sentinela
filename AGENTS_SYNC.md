# 🛰️ PROTOCOLO DE SINCRONIA INTER-AGENTES (SENTINELA v2.0)

Este arquivo é o canal oficial de comunicação entre o **Gemini CLI (Orquestrador/Arquiteto)** e o **Antigravity CLI (Executor/Refatorador)**.

---

## 🚦 STATUS DA MISSÃO
- **Fase 1 (Rocket Mode):** ✅ CONCLUÍDA
- **Fase 2 (Resiliência & Infra):** ✅ CONCLUÍDA (Circuit Breakers e Graceful Shutdown)
- **Fase 3 (Monetização E2E):** ✅ CONCLUÍDA (Stripe, Webhooks, Gating e Wallet CI)
- **Fase 4 (Auditoria Massiva e Proxies):** 🔄 INICIANDO AGORA

---

## ⚡ COMANDOS FASE 4: AUDITORIA MASSIVA (ESCOPO ANTIGRAVITY)

### Tarefa 5: Rotação Dinâmica de Proxies (Stealth Mode Final)
- **Instrução:** Adicionar suporte robusto a proxies residenciais no `Playwright` dentro do `core/instagram_scraper_v2.py`. Se a variável de ambiente `PROXY_URL` existir (ex: `http://user:pass@proxy.provider.com`), instanciar o `browserContext` passando-a. Caso contrário, rodar de forma nativa. Garantir que o sistema limpe o cache e feche o contexto anterior em caso de erro 429 para tentar um novo IP na próxima iteração.

### Tarefa 6: Auditoria de Banco de Dados e Fuga de Tokens (Double Spend)
- **Instrução:** Revisar o schema do banco (`scripts/migration_v19.6_stn.sql`) e a RPC `process_stn_transaction`. Certificar-se de que não existe possibilidade de "Race Condition" que permita um saldo de CI ficar negativo caso o usuário clique múltiplas vezes rapidamente no desbloqueio de Dossiês ou Alertas (Gating) no Frontend. O Supabase já possui o `FOR UPDATE`, mas garanta que o código de erro retornado pela RPC no `api/index.py` logue tentativas de fraude de saldo.

---

## 🔄 FEEDBACK DO GEMINI (Orquestrador)
**[28/05/2026] Fase 3 Concluída:**
- ✅ A esteira comercial está 100% no ar. O Stripe está ligado ao catálogo oficial e entrega tokens automaticamente através de Webhooks.
- ✅ O sistema de Gating bloqueou com sucesso os Dossiês (350 CI), Novos Alvos (500 CI), Radar (150 CI) e Alertas (850 CI). A dedução está atômica.

**Aguardando Antigravity assumir as Tarefas 5 e 6 acima para finalizarmos a implantação comercial e operacional de ponta a ponta.**


---
## 🚀 NOVA MISSÃO UNIFICADA (28/05/2026 14:17:57)
**Solicitação do Usuário:** Iniciar Fase 4: Implementação final de Proxies Dinâmicos (Stealth Mode) no Scraper e Auditoria profunda de Double Spend na RPC do banco.
**Status:** AGUARDANDO AGENTES...
